from flask import Flask, render_template, request, redirect, url_for
from neomodel import StructuredNode, StringProperty, IntegerProperty, RelationshipTo, RelationshipFrom, config
from neo4j import GraphDatabase
from flask_paginate import Pagination, get_page_args

app = Flask(__name__)

config_DATABASE_URL = 'neo4j:://neo4j:password@localhost:7687/'


uri = 'neo4j://localhost:7687'
username = 'neo4j'
password = 'password'
driver = GraphDatabase.driver(uri, auth=(username, password))

class Person(StructuredNode):
    name = StringProperty(unique_index=True)
    age = IntegerProperty(unique_index=False)
    knows = RelationshipTo('Person', 'KNOWS')

class Work(StructuredNode):
    name = StringProperty(unique_index=True)
    work = RelationshipTo('Work', 'WORK')

@app.route('/')
def index():
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 10
     
    with driver.session(database='neo4j') as sessions:
        result = sessions.run("MATCH (n:Person) RETURN elementId(n) as id, ID(n) as index, n.name AS name, n.age AS age")
        people = [{'id': record['id'], 'index': record['index'] ,'name': record['name'], 'age': record['age']} for record in result]

        total_result = sessions.run("MATCH (n:Person) RETURN count(n) AS total")
        total = total_result.single()['total']
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap5')

    return render_template('testing.html', people=people, pagination=pagination)
    
@app.route('/add-person', methods=['POST'])
def add_person():
    name = request.form.get('person_name', '').strip()
    age = request.form.get('person_age', '').strip()
    if name: 
        person = Person(name=name, age=age).save()

    person = Person.nodes.first_or_none(name=name, age=age)
    if not person:
       person = Person(name=name, age=age).save()
       print(f'Person {person.name} created')
    else:
        print(f'Person {person.name} already exists')
    return redirect(url_for('index'))

@app.route('/edit-person/<string:node_id>', methods=['GET', 'POST'])
def edit_person(node_id):     
    with driver.session(database='neo4j') as sessions:
        result = sessions.run("MATCH (n:Person) WHERE elementId(n) = $id RETURN elementId(n) as id, n.name as name", id=node_id)
        record = result.single()

    if not record:
        return "Person not found", 404

    person = {
        'id': record['id'],
        'name': record['name']
    }

    if request.method == 'POST':
        new_name = request.form.get('new_name', '').strip()
        if new_name and new_name != person['name']:
            with driver.session(database='neo4j') as sessions:
                sessions.run(
                    "MATCH (n:Person) WHERE elementId(n) = $id SET n.name = $new_name",
                    id=node_id,
                    new_name=new_name
                )
            print(f'Person updated successfully')
            return redirect(url_for('index'))

    return render_template('edit.html', person=person)


@app.route('/delete-person/<string:node_id>', methods=['POST'])
def delete_person(node_id):
    with driver.session() as session:
        query = """
        MATCH (n:Person) 
        WHERE elementId(n) = $id 
        DETACH DELETE n
        """
        session.run(query, id=node_id)
        print(f'Person {node_id} has been successfully deleted.')

    return redirect(url_for('index'))

@app.route('/create-relationship', methods=['POST'])
def create_relationship():
    first_node = request.form.get('first_node', '').strip()
    relationship = request.form.get('relationship', '').strip()
    second_node = request.form.get('second_node', '').strip()

    if not first_node or not relationship or not second_node:
        return "All fields are required", 400 

    with driver.session() as session:
        query = f"MATCH (f:Person {{name: $first_node}}), (s:Person {{name: $second_node}}) CREATE (f)-[:{relationship}]->(s)"
        session.run(query, first_node=first_node, second_node=second_node)

    return redirect(url_for('index'))


# @app.route('/')
@app.route('/forms')
def forms():
    return render_template('forms.html')

if __name__ == '__main__':
    app.run(debug=True)
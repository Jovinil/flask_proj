from flask import Flask, render_template, request, redirect, url_for
from neomodel import StructuredNode, StringProperty, IntegerProperty, RelationshipTo, RelationshipFrom, config
from neo4j import GraphDatabase

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
    with driver.session(database='neo4j') as sessions:
        result = sessions.run("MATCH (n:Person) RETURN ID(n) as id, n.name AS name, n.age AS age")
        people = [{'id': record['id'] ,'name': record['name'], 'age': record['age']} for record in result]

        return render_template('testing.html', people=people)
    
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

@app.route('/update-person', methods=['POST'])
def update_person():
    old_name_id = request.form.get('old_name_id')
    current_name = request.form.get('current_person_name', '').strip()
# update needs to be fixed as to update base on the id instead of name
    if old_name_id and current_name:
       with driver.session() as session:
            query = "MATCH (n) WHERE id(n) = $id DELETE n"
            session.run(query, id=int(old_name_id))

    return redirect(url_for('index'))

@app.route('/delete-person', methods=['POST'])
def delete_person():
    node_id = request.form.get('node_id')
    with driver.session() as session:
        query = "MATCH (n) WHERE id(n) = $id DELETE n"
        session.run(query, id=int(node_id))

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
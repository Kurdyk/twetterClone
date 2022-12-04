# twetterClone
A project for Advanced Algorithms at Dauphine-PSL

# Setup
Something like
`python3 -m venv env && source .env/bin/activate && pip install -r requirements.txt`

# Running the project:
`flask --app flaskr --debug run`

# Adding a random user
`flask --app flaskr add-random-user`

# Adding a random tweet
`flask --app flaskr add-random-tweet`

# Getting symetric relationships
flask --app flaskr symetric-relationship [--name]

# Getting the followers at each level < depth
flask --app flaskr followers-graph <--user_id n> [--depth <depth>]

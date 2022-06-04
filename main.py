import pymongo
from flask import json
from flask import request
from flask import Flask
from flask import abort
import requests

app = Flask(__name__)


@app.route('/git' , methods=['POST'])
def webhook():
   token = "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"
   headers = {'Authorization': "token {}".format(token)}
   client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
   mydb = client['Github']
   issues_collection = mydb.issues
   labels_collection = mydb.labels
   project_card_collection = mydb.project_cards
   assigness_collection = mydb.assignees
   data = request.json
   if request.headers['X-GitHub-Event'] == 'issues':

       if data['action'] == "labeled":
           label = labels_collection.find_one({'id': data['label']['id']})
           if not label:
               label = data['label']
               name = label['name'].lower()
               if name[0:3] == "size" or name[0:4] == "epic":
                   try:
                       name1 = name.replace(" ", "")
                       nv = name1.split(":")
                       print(nv[0])
                       labels_collection.insert_one({
                           'id': label['id'],
                           'issue_id': data['issue']['node_id'],
                           'description': label['description'],
                           'name': nv[0],
                           'value': nv[1]
                       })
                   except IndexError:
                       print('only one value')
                   return ("ok")
               elif name[0:6] == "logged":
                   try:
                       name1 = name.replace(" ", "")
                       nv = name1.split(":")
                       value = int(nv[1])
                       labels_collection.insert_one({
                           'id': label['id'],
                           'issue_id': data['issue']['node_id'],
                           'description': label['description'],
                           'name': nv[0],
                           'value': nv[1]
                       })
                   except IndexError:
                       print('only one value')
                   return ('ok')

               else:
                   labels_collection.insert_one({
                       'id': label['id'],
                       'issue_id': data['issue']['node_id'],
                       'description': label['description'],
                       'name': label['name'],
                       'value': 'null'
                   })
               return ('ok')
           else:
               return abort(404, description="label can not be added")

       elif data['action'] == "unlabeled":
         label = labels_collection.find_one({'id': data['label']['id']})
         if label:
            myquery = {"id": data['label']['id']}
            labels_collection.delete_one(myquery)
            return ("ok")
         else:
             return abort(404, description="label Not Found")



   else:
       return ("bug")


if __name__ == '__main__':
    app.run(debug=True)

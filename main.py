import pymongo
from flask import json
from flask import request
from flask import Flask
from flask import abort
import requests

app = Flask(__name__)


@app.route('/git', methods=['POST'])
def webhook():
    client = pymongo.MongoClient("mongodb://karim:22654790@cluster0-shard-00-00.3jtiz.mongodb.net:27017,cluster0-shard-00-01.3jtiz.mongodb.net:27017,cluster0-shard-00-02.3jtiz.mongodb.net:27017/?ssl=true&replicaSet=atlas-4lvqcl-shard-0&authSource=admin&retryWrites=true&w=majority")
    mydb = client['Github']
    token = "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"
    headers = {'Authorization': "token {}".format(token)}
    issues_collection = mydb.issues
    labels_collection = mydb.labels
    project_card_collection = mydb.project_cards
    assigness_collection = mydb.assignees
    data = request.json
    if request.headers['X-GitHub-Event'] == 'issues':
        if data['action'] == "opened":
            issue = issues_collection.find_one({'id': data['issue']['node_id']})
            if not issue:
                issues_collection.insert_one({
                    'id': data['issue']['id'],
                    'node_id': data['issue']['node_id'],
                    'number': data['issue']['number'],
                    'title': data['issue']['title'],
                    'state': data['issue']['state'],
                    'locked': data['issue']['locked'],
                    'created_at': data['issue']['created_at'],
                    'updated_at': data['issue']['updated_at'],
                    'closed_at': data['issue']['closed_at'],
                    'body': data['issue']['body'],

                })
                labels = data['issue']['labels']
                for label in labels:
                    labels_collection.insert_one({
                        'id': label['id'],
                        'issue_id': data['issue']['node_id'],
                        'description': labels['description'],
                        'name': label['name']

                    })
                assigness = data['issue']['assignees']
                for assigne in assigness:
                    assigness_collection.insert_one({
                        'login': assigne['login'],
                        'issue_id': assigne['node_id'],
                        'id': assigne['id']
                    })
                return ("ok")
            else:
                return abort(404, description="issue existe")
        elif data['action'] == "closed" or data['action'] == "edited":
            issue = issues_collection.find_one({'node_id': data['issue']['node_id']})
            if issue:
                issues_collection.update_one({'node_id': data['issue']['node_id']},
                                             {"$set": {'state': data['issue']['state'],
                                                       'updated_at': data['issue']['updated_at'],
                                                       'closed_at': data['issue']['closed_at'],
                                                       'title': data['issue']['title'],
                                                       'body': data['issue']['body'],
                                                       }})
                return ("ok")
            else:
                return abort(404, description="issue not found")

        elif data['action'] == "deleted":
            issue = issues_collection.find_one({'node_id': data['issue']['node_id']})
            if issue:
                # jointure
                issue_del = {"id": data['issue']['node_id']}
                info_del = {"issue_id": data['issue']['node_id']}
                issues_collection.delete_one(issue_del)
                labels_collection.delete_many(info_del)
                assigness_collection.delete_many(info_del)
                project_card_collection.delete_one(info_del)
                return ("ok")
            else:
                return abort(404, description="issue not found")


        elif data['action'] == "labeled":
            label = labels_collection.find_one({'id': data['label']['id']})
            if not label:
                label = data['label']
                name = label['name'].lower()
                if name[0:4] == "size" or name[0:4] == "epic":
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
                elif name[0:4] == "epic":
                    try:
                        name1 = name.replace(" ", "")
                        nv = name1.split(":")
                        nameNv = name.split(":")
                        labels_collection.insert_one({
                            'id': label['id'],
                            'issue_id': data['issue']['node_id'],
                            'description': label['description'],
                            'name': nv[0],
                            'value': nameNv[1]
                        })
                    except IndexError:
                        print('only one value')
                    return ('ok')
                elif name[0:6] == "logged":
                    try:
                        name1 = name.replace(" ", "")
                        nv = name1.split(":")
                        labels_collection.insert_one({
                            'id': label['id'],
                            'issue_id': data['issue']['node_id'],
                            'description': label['description'],
                            'name': nv[0],
                            'value': int(nv[1])
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
            label = labels_collection.find_one({'issue_id': data['issue']['node_id']})
            if label:
                myquery = {"id": data['label']['id']}
                labels_collection.delete_one(myquery)
                return ("ok")
            else:
                return abort(404, description="label Not Found")


        elif data['action'] == "assigned":
            assignee = assigness_collection.find_one({'issue_id': data['issue']['node_id']
                                                      })
            if not assignee:
                assigness_collection.insert_one({
                    'login': data['assignee']['login'],
                    'issue_id': data['issue']['node_id'],
                    'id': data['assignee']['id']

                })
                return ("ok")
            else:
                return abort(404, description="assigne can not be added")


        elif data['action'] == "unassigned":
            assignee = assigness_collection.find_one({'issue_id': data['issue']['node_id']})
            if assignee:
                myquery = {"issue_id": data['issue']['node_id']}
                assigness_collection.delete_one(myquery)
                return ("ok")
            else:

                return abort(404, description="assigne not found")

        else:
            return ("bug")
    elif request.headers['X-GitHub-Event'] == 'project_card':
      if data['action'] == "converted":
       card = project_card_collection.find_one({'id': data['project_card']['id']})
       if not card:
        content = data['project_card']['content_url']
        issue = requests.get(content, headers=headers).json()
        column_content = data['project_card']['column_url']
        column = requests.get(column_content, headers=headers).json()
        project_card_collection.insert_one({
            'issue_id': issue['node_id'],
            'card_name': column['name'],
            'id': data['project_card']['id'],
        })
        return ("ok")
       else:
        return abort(404, description="card not found")
      elif data['action'] == "moved":
       card = project_card_collection.find_one({'id': data['project_card']['id']})
       if card:
        column_content = data['project_card']['column_url']
        column = requests.get(column_content, headers=headers).json()
        project_card_collection.update_one({'id': data['project_card']['id']},
                                           {"$set": {'card_name': column['name'],
                                                     }})

        return ("ok")
       else:
         return abort(404, description="card not found")
      elif data['action'] == "deleted":
       card = project_card_collection.find_one({'id': data['project_card']['id']})
       if card:
        myquery = {"id": data['project_card']['id']}
        project_card_collection.delete_one(myquery)
        print("c est bon")

        return ("ok")
       else:
        return abort(404, description="card not found")


    else:
     return ("bug")


if __name__ == '__main__':
    app.run(debug=True)

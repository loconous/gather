'''
Script to compare if we are getting different results from the GraphQL query for forks and repos
The query scripts are identical for the exception of the fork flag
According to some previous comments, these may not make any difference, so this script provides proof for functionality
'''

import pymongo
import json

# Set limit of comparison; change to None for full comparison of collections
def compare_collections(db_name, coll1_name, coll2_name, limit=10):
  client = pymongo.MongoClient()
  db = client[db_name]
  coll1 = db[coll1_name]
  coll2 = db[coll2_name]

  # Compare document counts
  count1 = coll1.count_documents({})
  count2 = coll2.count_documents({})
  
  print(f"{coll1_name} count: {count1}")
  print(f"{coll2_name} count: {count2}")

  if count1 != count2:
    print("Collections have different number of documents.")
    return False

  # Compare content by _id
  same = True
  cursor1 = coll1.find().sort("pushedAt", 1).limit(limit) if limit else coll1.find()

  for doc1 in cursor1:
    doc2 = coll2.find_one({"_id": doc1["_id"]})
    if not doc2:
      print(f"Missing in {coll2_name}: _id {doc1['_id']}")
      same = False
      continue

    # Compare documents (excluding fields like '_id' if needed)
    doc1_json = json.dumps(doc1, sort_keys=True, default=str)
    doc2_json = json.dumps(doc2, sort_keys=True, default=str)

    if doc1_json != doc2_json:
      print(f"Difference for _id {doc1['_id']}")
      same = False

  return same

# Driver
if __name__ == "__main__":
  db_name = "gh202507"         # Change manually
  coll1 = "repos"                 # Repo collection
  coll2 = "forks"                 # Fork collection 
  result = compare_collections(db_name, coll1, coll2)
  print("Collections are identical." if result else "Collections differ.")


'''
Script to scrape GitHub forked repos using the GraphQL API
Obtains all forked repos that have been updated AFTER a specified date
Scrapes all repos from that date up to the current time and logs repository counts
'''
import requests
import json
import pymongo
from datetime import datetime, timedelta
import time
import sys

# get start and end date, and GITHUB API token from command line
token, begin, end = sys.stdin.readline().strip().split(' ')

try:
  datetime.strptime(begin, '%Y-%m-%d')
  datetime.strptime(end, '%Y-%m-%d')
except ValueError:
  raise ValueError("Incorrect beginning date format, should be YYYY-MM-DD")

# DB info
client = pymongo.MongoClient()
dbName = sys.argv[1] # db name as second arg
collName = sys.argv[2] # coll name as third arg

db = client[dbName]
coll = db[collName]
count_coll = db[f"{collName}_counts"]  # Separate collection for counts

url = 'https://api.github.com/graphql'
headers = {'Authorization': 'token ' + token}
start = begin + 'T00:00:00Z'
end_time = datetime.strptime(end + 'T00:00:00Z', "%Y-%m-%dT%H:%M:%SZ")
interval = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
total = 0
remaining = 5000

# GraphQL query for forked repos
query = '''{
  rateLimit {
    cost
    remaining
    resetAt
  }
  search(query: "is:public archived:false fork:true mirror:false pushed:%s..%s", type: REPOSITORY, first: 100) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
      startCursor
    }
    nodes {
        ... on Repository {
          nameWithOwner
          updatedAt
          createdAt
          pushedAt
          id
          forkCount
          description
        }
      }
  }
}'''
jsonS = { 'query': query }

# wait for reset if we exhaust our number of calls
def wait(reset):
  now = datetime.now()
  then = datetime.strptime(reset, "%Y-%m-%dT%H:%M:%SZ")
  wait = (then - now).total_seconds() + 30
  time.sleep(wait)

# helper function to loop through and insert repos into mongo db
def gatherData(res, period_start, period_end):
  global total
  repos = res['data']['search']['nodes']
  for i in repos:
    coll.insert_one(i)
  total += len(repos)

  # Store count information in the separate collection
  count_info = {
    "period_start": period_start,
    "period_end": period_end,
    "repository_count": res['data']['search']['repositoryCount'],
    "captured_count": len(repos),
    "timestamp": datetime.now()
  }
  count_coll.insert_one(count_info)

  output = "Got {} repos. Total count is {}. Have {} calls remaining."
  print(output.format(len(repos), total, remaining))

# driver loop that iterates through repos in 10 minute intervals
while interval < end_time:
  fromStr = interval.strftime("%Y-%m-%dT%H:%M:%SZ")
  toStr = (interval + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
  nextQuery = query % (fromStr, toStr)
  jsonS['query'] = nextQuery

  if token == '':
    print("Please provide your Github API token in the script. Exiting.")
    sys.exit()

  r = requests.post(url=url, json=jsonS, headers=headers)
  if r.ok:
    try:
      res = json.loads(r.content)
      print("did it come here? {}".format(res['data']['search']['pageInfo']))
      remaining = res['data']['rateLimit']['remaining']
      reset = res['data']['rateLimit']['resetAt']
      if remaining < 11:
        wait(reset)

      repos = res['data']['search']['repositoryCount']
      hasNextPage = res['data']['search']['pageInfo']['hasNextPage']
      gatherData(res, fromStr, toStr)

      # handle pagination
      while repos > 100 and hasNextPage:
        endCursor = res['data']['search']['pageInfo']['endCursor']
        print("Have to paginate, using cursor {}".format(endCursor))
        index = nextQuery.find("REPOSITORY") + len("REPOSITORY")
        pageQuery = nextQuery[:index] + ',after:"{}"'.format(endCursor) + nextQuery[index:]
        jsonS['query'] = pageQuery

        r = requests.post(url=url, json=jsonS, headers=headers)
        if r.ok:
          res = json.loads(r.text)
          try:
            remaining = res['data']['rateLimit']['remaining']
            reset = res['data']['rateLimit']['resetAt']
            if remaining < 11:
              wait(reset)
            repos = res['data']['search']['repositoryCount']
            hasNextPage = res['data']['search']['pageInfo']['hasNextPage']
            gatherData(res, fromStr, toStr)
          except Exception as e:
            print(e)
    except Exception as e:
      print(e)
  interval += timedelta(minutes=10)
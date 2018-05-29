import praw, requests, httplib2
from bs4 import BeautifulSoup
from queue import Queue
from threading import Thread

# constants
MAX_WEBSITES = 100  # number of websites to scrape
THREADS = 35
CLIENT_ID = ""
CLIENT_SECRET = ""
PASSWORD = ""
USER_AGENT = "File finder by x3419"
USERNAME = ""


def run():
    session = requests.session()

    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
                         password=PASSWORD,
                         user_agent=USER_AGENT,
                         username=USERNAME)

    opendirs = reddit.subreddit("opendirectories")

    category = input("Enter category (i.e. \"show\"): ")

    search_term = input("Enter a search term: ")
    search_term = search_term.lower()

    print("Searching....")

    queue = Queue()

    for x in range(THREADS):
        worker = SearchRecurser(queue)
        worker.daemon = True
        worker.start()

    count = 0
    subs = (submission for submission in opendirs.search(category) if count < MAX_WEBSITES)
    for submission in subs:

        url = submission.url
        http = httplib2.Http()

        # ignore the submissions that have multiple links within the post body
        if "reddit.com" not in url:
            try:
                status, response = http.request(url)
                soup = BeautifulSoup(response, "lxml")
                links = [link['href'] for link in soup.findAll('a') if link.has_attr('href')]

                queue.put((links, search_term, url, http, session))
                count += 1

            except:
                continue

    queue.join()


class SearchRecurser(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):

        while True:
            links, search_term, url, http, session = self.queue.get()
            self.recurse(links, search_term, url, http, session)
            self.queue.task_done()

    # TODO: speed this up with more threads or something
    # Idea: the "twisted!" library
    def recurse(self, links, search_term, url, http, session):

        if [s for s in links if search_term in s.lower()] != []:
            print("Found: {}".format(url))
            return
        elif links != []:
            for l in links:
                if l != "../":
                    try:
                        # we only want webpages
                        response = session.head(url + l, timeout=1)
                        contentType = response.headers['content-type']

                        if contentType == "text/html":
                            status, response = http.request(url + l)
                            soup = BeautifulSoup(response, "lxml")
                            newLinks = [newLink['href'] for newLink in soup.findAll('a') if newLink.has_attr('href')]
                            self.recurse(newLinks, search_term, url + l, http, session)
                    except:
                        continue


if __name__ == '__main__':
    run()
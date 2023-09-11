import requests
import json
from collections.abc import MutableMapping
import csv
from optparse import OptionParser
import time

keys = ["id_str", "favorite_count", "lang", "created_at", "entities_media", "entities_urls", "text", "user_id_str", "user_name", "user_screen_name", "user_verified", "is_blue_verified"]
def flatten(dictionary, parent_key='', separator='_'):
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)

def get_tweet(tweet_id):
    url = "https://cdn.syndication.twimg.com/tweet-result"

    querystring = {"id":tweet_id,"lang":"en", "token" : "token"}

    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://platform.twitter.com",
        "Connection": "keep-alive",
        "Referer": "https://platform.twitter.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }

    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    return json.loads(response.text)


def get_tweet_info(tweet_orig, stop_recurse = False):
    tweet = flatten(tweet_orig)
    d = {k:tweet.get(k) for k in keys}
    if d.get("entities_media"):
        d["entities_media"] = ",".join(x["expanded_url"] for x in d["entities_media"]) 
    if d.get("entities_urls"):
        d["entities_urls"] = ",".join(x["expanded_url"] for x in d["entities_urls"])
    else:
        d["entities_urls"] = None
    if d.get("text"):
        d["text"] = d["text"].replace("\n", " ")
    d["is_quote_tweet"] = False
    d["is_quoted_tweet"] = False
    d["quoted_by_id"] = None
    if tweet_orig.get("quoted_tweet") and not stop_recurse:
        quote_tweet_d, _  = get_tweet_info(tweet_orig["quoted_tweet"], stop_recurse = True)
        quote_tweet_d["is_quoted_tweet"] = True
        quote_tweet_d["quoted_by_id"] = d["id_str"]
        d["is_quote_tweet"] = True
    else:
        quote_tweet_d = None

    return d, quote_tweet_d


    
def write_tweets_to_csv(tweet_ids, output_file="output/tweets_output.csv", write_header = True):
    with open(output_file, 'a+', newline='', encoding='utf-8') as csvfile:
        fieldnames = keys + ["is_quote_tweet", "is_quoted_tweet", "quoted_by_id"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for tweet_id in tweet_ids:
            try:
                tweet = get_tweet(tweet_id)

                print(tweet)
                tweet_dict, quote_dict = get_tweet_info(tweet)
            except Exception as e:
                print ("Exception getting tweet ID " + str(tweet_id))
                print (e)
                time.sleep(5)
                continue
            time.sleep(1)
            writer.writerow(tweet_dict)
            if quote_dict:
                writer.writerow(quote_dict)

    print(f"Data has been written to {output_file}")

def main():
    parser = OptionParser()
    parser.add_option("-t", "--tweets", dest="tweet_ids", help="list of tweet IDs separated by comma", metavar="TWEETS")
    parser.add_option("-f", "--file", dest="file_path", help="path to a text file with tweet IDs, each separated by a newline", metavar="FILE")
    parser.add_option("-o", "--output", dest="output_file", help="output_file", metavar="FILE")
    parser.add_option("-i", "--input", dest="input_file", help="past tweets", metavar="FILE")

    (options, args) = parser.parse_args()

    if not options.tweet_ids and not options.file_path:
        parser.error("You must provide a list of tweet IDs using the -t option or a file using the -f option.")

    if options.file_path:
        with open(options.file_path, 'r') as file:
            tweet_ids = [line.strip() for line in file.readlines()]
    else:
        tweet_ids = options.tweet_ids.split(',')

    # past tweets
    if options.input_file:
        with open(options.input_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            past_tweet_ids = [row[0] for row in reader]
    else:
       past_tweet_ids = []

    tweet_ids = [tweet_id for tweet_id in tweet_ids if tweet_id not in past_tweet_ids]

    if options.output_file:
        output_file = options.output_file
    else:
        output_file = "output/tweets_output.csv"
    write_tweets_to_csv(tweet_ids, output_file, len(past_tweet_ids) == 0)

if __name__ == "__main__":
    main()


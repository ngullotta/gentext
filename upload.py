# -*- coding: utf-8 -*-

# Sample Python code for youtube.videos.insert
# NOTES:
# 1. This sample code uploads a file and can't be executed via this interface.
#    To test this code, you must run it locally using your own API credentials.
#    See: https://developers.google.com/explorer-help/code-samples#python
# 2. This example makes a simple upload request. We recommend that you consider
#    using resumable uploads instead, particularly if you are transferring large
#    files or there's a high likelihood of a network interruption or other
#    transmission failure. To learn more about resumable uploads, see:
#    https://developers.google.com/api-client-library/python/guide/media_upload

import json
import os
import sys

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

scopes = ["https://www.googleapis.com/auth/youtube.upload"]


"""
ID	Category name
1	Film & Animation
2	Autos & Vehicles
10	Music
15	Pets & Animals
17	Sports
19	Travel & Events
20	Gaming
22	People & Blogs
23	Comedy
24	Entertainment
25	News & Politics
26	Howto & Style
27	Education
28	Science & Technology
29	Nonprofits & Activism
"""


def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "secrets.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes
    )
    credentials = flow.run_local_server()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials
    )

    script = "/".join([sys.argv[1], "script.json"])
    with open(script) as fp:
        data = json.load(fp)

    if len(data) == 0:
        print("No script data found")
        exit(1)

    description = (
        data["text"]
        + "\n\n"
        + data["attributions"]
        + "\n\n"
        + "Gameplay courtesy of: https://www.youtube.com/@NoCopyrightGameplays"
    )
    file = "/".join([sys.argv[1], "output.mp4"])

    tags = data.get("tags", [])
    tags.extend(
        [
            "4chan",
            "Funny",
            "fyp",
            "Spooky",
            "Memes",
            "Greentext stories",
            "Funny greentexts",
            "4chan stories",
            "Reddit greentext",
            "Internet stories",
            "Meme stories",
            "Funny stories",
            "Anonymous",
            "4chan memes",
            "Greentext meme",
            "4chan humor",
            "Weird 4chan stories",
            "Funny internet stories",
            "Internet culture",
        ]
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "24",
                "description": description,
                "title": data["title"],
                "tags": tags,
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        },
        # TODO: For this request to work, you must replace "YOUR_FILE"
        #       with a pointer to the actual file you are uploading.
        media_body=MediaFileUpload(file),
    )
    response = request.execute()

    print(response)


if __name__ == "__main__":
    main()

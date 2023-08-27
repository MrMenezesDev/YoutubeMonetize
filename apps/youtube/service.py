import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from apps.config import Config
from apps.youtube.models import Channels, get_not_subscribed


def get_youtube(canal: Channels):
    credentials = Credentials(
        **json.loads(canal.channel_credentials.replace("'", '"')))

    return build(
        Config.YOUTUBE_API_SERVICE_NAME, Config.YOUTUBE_API_VERSION, credentials=credentials)


def get_subscribers(canal: Channels, youtube: Resource = None):
    # TODO: Not Work API
    # youtube = get_youtube(canal) if not youtube else youtube
    subscribers = []
    # pageToken = None
    # while True:
    #     response = youtube.subscriptions().list(
    #         part='snippet',
    #         mySubscribers=True,
    #         fields="nextPageToken,pageInfo,items(snippet(channelId))",
    #         maxResults=50,
    #         pageToken=pageToken,
    #     ).execute()
    #     subscribers.extend(x['snippet']['channelId']
    #                        for x in response['items'])
    #     pageToken = response['nextPageToken'] if 'nextPageToken' in response else None
    #     if 'nextPageToken' not in response:
    #         break

    return subscribers


def get_statistics(canal: Channels, youtube: Resource = None):
    youtube = get_youtube(canal) if not youtube else youtube
    statistics = youtube.channels().list(
        part="statistics",
        mine=True,
        fields="items(statistics(viewCount,subscriberCount,videoCount,hiddenSubscriberCount,))"
    ).execute()

    return statistics['items'][0]['statistics'] if 'items' in statistics else None


def get_subscriptions(canal: Channels, youtube: Resource = None):
    youtube = get_youtube(canal) if not youtube else youtube
    subscriptions = []
    pageToken = None
    while True:
        response = youtube.subscriptions().list(
            part="snippet",
            channelId=canal.channel_id,
            fields="nextPageToken,pageInfo,items(snippet(channelId))",
            maxResults=50,
            pageToken=pageToken
        ).execute()
        pageToken = response['nextPageToken'] if 'nextPageToken' in response else None
        subscriptions.extend(x['snippet']['channelId']
                             for x in response['items'])
        if 'nextPageToken' not in response:
            break

    return subscriptions


def subscribe_all(canal: Channels, youtube: Resource = None):
    youtube = get_youtube(canal) if not youtube else youtube

    to_subscribe = get_not_subscribed(canal.channel_id)
    to_subscribe = [x[0] for x in to_subscribe]
    to_subscribe.remove(canal.channel_id)
    for channel_id in to_subscribe:
        try:
            youtube.subscriptions().insert(
                part="snippet,id",
                body={
                    "snippet": {
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": channel_id
                        }
                    }
                }
            ).execute()
        except Exception as e:
            print(e, channel_id, canal.channel_id)


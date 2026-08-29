
import httpx

def get_track_info_from_playlist(playlist_id):
    url = f"https://api.deezer.com/playlist/{playlist_id}"
    with httpx.Client() as client:
        response = client.get(url)
        # NOTE: This has the added benefit of collapsing duplicate albums if the playlist contains more than 1 song from that album
        return {t["id"]: (t["artist"]["name"], t["album"]["title"], t["title"]) for t in response.json()['tracks']['data']}

# Example usage:
playlist_id = 14183037961  # Replace with playlist id
# album_info = get_album_info(playlist_id)
track_info = get_track_info_from_playlist(playlist_id)
# print(album_info)
print(track_info)
# album_ids = [str(a) for a in album_info.keys()]
track_ids = [str(t) for t in track_info.keys()]
# print(' '.join(album_ids))
print(' '.join(track_ids))

# for a in album_ids:
#     print("https://www.deezer.com/en/album/" + a)
for t in track_ids:
    print("https://www.deezer.com/en/track/" + t)
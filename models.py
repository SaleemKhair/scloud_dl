from dataclasses import dataclass
from json_to_models.dynamic_typing import IntString
from typing import List, Literal, Optional, Union


@dataclass
class Collection:
    created_at: str
    kind: Literal["like"]
    track: 'Track'


@dataclass
class Track:
    commentable: bool
    created_at: str
    downloadable: bool
    duration: int
    full_duration: int
    embeddable_by: Literal["all"]
    genre: str
    has_downloads_left: bool
    id_: int
    kind: Literal["track"]
    last_modified: str
    license_: Literal["all-rights-reserved", "cc-by-nc", "cc-by-nc-sa"]
    permalink: str
    permalink_url: str
    public: bool
    reposts_count: int
    secret_token: None
    sharing: Literal["public"]
    state: Literal["finished"]
    streamable: bool
    tag_list: str
    title: str
    track_format: Literal["single-track"]
    uri: str
    urn: str
    user_id: int
    waveform_url: str
    display_date: str
    media: 'Medium'
    station_urn: str
    station_permalink: str
    track_authorization: str
    monetization_model: Literal["NOT_APPLICABLE"]
    policy: Literal["ALLOW", "SNIP"]
    user: 'User'
    artwork_url: Optional[str] = None
    caption: Optional[str] = None
    comment_count: Optional[int] = None
    description: Optional[str] = None
    download_count: Optional[int] = None
    label_name: Optional[str] = None
    likes_count: Optional[int] = None
    playback_count: Optional[int] = None
    publisher_metadata: Optional['PublisherMetadatum'] = None
    purchase_title: Optional[str] = None
    purchase_url: Optional[str] = None
    release_date: Optional[str] = None
    visuals: Optional['Visual'] = None


@dataclass
class PublisherMetadatum:
    id_: int
    urn: str
    artist: Optional[str] = None
    contains_music: Optional[bool] = None
    isrc: Optional[str] = None
    publisher: Optional[str] = None
    writer_composer: Optional[str] = None
    release_title: Optional[str] = None
    explicit: Optional[bool] = None
    album_title: Optional[str] = None
    upc_or_ean: Optional[Union[IntString, Literal[""]]] = None
    p_line: Optional[str] = None
    p_line_for_display: Optional[str] = None
    c_line: Optional[str] = None
    c_line_for_display: Optional[str] = None


@dataclass
class Visual:
    urn: str
    enabled: bool
    visuals: List['Visual_1E']
    tracking: None


@dataclass
class Visual_1E:
    urn: str
    entry_time: int
    visual_url: str


@dataclass
class Medium:
    transcodings: List['Transcoding']


@dataclass
class Transcoding:
    url: str
    preset: Literal["mp3_0_0", "mp3_0_1", "mp3_1_0", "mp3_standard", "opus_0_0"]
    duration: int
    snipped: bool
    format_: 'Format'
    quality: Literal["sq"]


@dataclass
class Format:
    protocol: Literal["hls", "progressive"]
    mime_type: str


@dataclass
class User:
    avatar_url: str
    first_name: str
    followers_count: int
    full_name: str
    id_: int
    kind: Literal["user"]
    last_modified: str
    last_name: str
    permalink: str
    permalink_url: str
    uri: str
    urn: str
    username: str
    verified: bool
    badges: 'Badge'
    station_urn: str
    station_permalink: str
    city: Optional[str] = None
    country_code: Optional[str] = None


@dataclass
class Badge:
    pro: bool
    pro_unlimited: bool
    verified: bool

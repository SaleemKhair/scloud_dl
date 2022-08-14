from dataclasses import dataclass
from json_to_models.dynamic_typing import FloatString
from typing import Literal


@dataclass
class RequestWillBeSent:
    method: str
    params: 'Param'


@dataclass
class Param:
    document_url: str
    frame_id: str
    has_user_gesture: bool
    initiator: 'Initiator'
    loader_id: str
    redirect_has_extra_info: bool
    request: 'Request'
    request_id: FloatString
    timestamp: float
    type_: Literal["Image"]
    wall_time: float


@dataclass
class Initiator:
    type_: Literal["other"]


@dataclass
class Request:
    headers: 'Header'
    initial_priority: Literal["Low"]
    is_same_site: bool
    method: Literal["GET"]
    mixed_content_type: Literal["none"]
    referrer_policy: Literal["origin"]
    url: str


@dataclass
class Header:
    referer: str
    user_agent: str
    secchua: str
    secchuamobile: Literal["?0"]
    secchuaplatform: Literal["\"Linux\""]

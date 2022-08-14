#!/usr/bin/env bash
USER_ID=""
CLIENT_ID=""
AUTH_TOKEN=""

API_BASE_DOMAIN="https://api-v2.soundcloud.com"
TRACK_PATH="/media/soundcloud:tracks:807672178/24f39ae4-1ba6-4c1e-abe7-eb83d45c3dbb/stream/hls"
QUERY_PARAMS="?client_id=${CLIENT_ID}"

URL_TRACK_DETAILS="${API_BASE_DOMAIN}${TRACK_PATH}${QUERY_PARAMS}"
RESP_FILE_NAME="./track.response.json"

if [ -f "${RESP_FILE_NAME}" ];then
    jq '.' "${RESP_FILE_NAME}"
else
    curl ${URL_TRACK_DETAILS} \
        --request GET --silent -v \
        --header "Authorization: OAuth ${AUTH_TOKEN}" \
        --header "Accept: application/json" \
        | jq '.' \
        #| tee $RESP_FILE_NAME
fi
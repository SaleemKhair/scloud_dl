#!/usr/bin/env bash
USER_ID=""
CLIENT_ID=""
AUTH_TOKEN=""

API_BASE_DOMAIN="https://api-v2.soundcloud.com"

COLLECTION_TYPE="track_likes"

LIKES_PATH="/users/${USER_ID}/${COLLECTION_TYPE}"

QUERY_PARAMS="?client_id=${CLIENT_ID}&limit=200"

URL_LIKES_COLLECTION="${API_BASE_DOMAIN}${LIKES_PATH}${QUERY_PARAMS}"

RESP_FILE_NAME="./collection.${COLLECTION_TYPE}.response.json"

if [ -f "${RESP_FILE_NAME}" ];then
    jq '.' "${RESP_FILE_NAME}"
else
    curl ${URL_LIKES_COLLECTION} \
        --request GET --silent \
        --header "Authorization: OAuth ${AUTH_TOKEN}" \
        --header "Accept: application/json" \
        | jq '.collection | {collection: .}' \
        | tee $RESP_FILE_NAME
fi
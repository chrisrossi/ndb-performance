export GOOGLE_APPLICATION_CREDENTIALS=`realpath $1`
gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
gcloud config set account "$(jq -r '.client_email' "${GOOGLE_APPLICATION_CREDENTIALS}")"
gcloud config set project "$(jq -r '.project_id' "${GOOGLE_APPLICATION_CREDENTIALS}")"

#!/usr/bin/env bash
#
# Serve an already verified local hfcache model with vLLM in a container.
#
# Usage:
#   scripts/consumer-serve-hfcache-model.sh [--runtime podman|docker] \
#     VLLM_IMAGE MODEL_DIRECTORY VLLM_CONFIG_YAML
#
# Example:
#   scripts/consumer-serve-hfcache-model.sh \
#     docker.io/vllm/vllm-openai:latest \
#     ~/.cache/hfcache/unsloth/Qwen3.8-27B-NVFP4/ \
#     ./qwen3.8-vllm.yaml
#
set -euo pipefail

RUNTIME=
CONTAINER_MODEL_DIR=/opt/hfcache/model
CONTAINER_CONFIG_FILE=/etc/vllm/config.yaml

usage() {
  printf '%s\n' \
    'Serve an already verified local hfcache model with vLLM.' \
    '' \
    'Usage:' \
    '  consumer-serve-hfcache-model.sh [--runtime podman|docker] \' \
    '    VLLM_IMAGE MODEL_DIRECTORY VLLM_CONFIG_YAML' \
    '' \
    'The model and YAML config are mounted read-only. Podman is preferred' \
    'when --runtime is omitted and both supported runtimes are installed.'
}

die() {
  printf 'consumer-serve-hfcache-model: %s\n' "$*" >&2
  exit 1
}

usage_error() {
  printf 'consumer-serve-hfcache-model: %s\n' "$*" >&2
  printf 'Try --help for usage.\n' >&2
  exit 64
}

while (( $# > 0 )); do
  case $1 in
    -h | --help)
      usage
      exit 0
      ;;
    --runtime)
      (( $# >= 2 )) || usage_error '--runtime requires podman or docker'
      RUNTIME=$2
      shift 2
      ;;
    --)
      shift
      break
      ;;
    --*) usage_error "unknown option: $1" ;;
    *) break ;;
  esac
done

(( $# == 3 )) ||
  usage_error 'expected VLLM_IMAGE, MODEL_DIRECTORY, and VLLM_CONFIG_YAML'

VLLM_IMAGE=$1
MODEL_DIRECTORY=$2
VLLM_CONFIG_FILE=$3

case ${RUNTIME} in
  '' | podman | docker) ;;
  *) usage_error "unsupported runtime: ${RUNTIME}" ;;
esac

[[ -n ${VLLM_IMAGE} ]] || usage_error 'VLLM_IMAGE must not be empty'
[[ ${VLLM_IMAGE} != -* ]] || usage_error 'VLLM_IMAGE must not begin with a dash'
[[ -d ${MODEL_DIRECTORY} ]] || die "model directory not found: ${MODEL_DIRECTORY}"
[[ -r ${MODEL_DIRECTORY} && -x ${MODEL_DIRECTORY} ]] ||
  die "model directory is not readable: ${MODEL_DIRECTORY}"
[[ -f ${VLLM_CONFIG_FILE} ]] || die "vLLM config file not found: ${VLLM_CONFIG_FILE}"
[[ -r ${VLLM_CONFIG_FILE} ]] || die "vLLM config file is not readable: ${VLLM_CONFIG_FILE}"

command -v realpath > /dev/null || die 'required command not found: realpath'
MODEL_DIRECTORY=$(realpath -- "${MODEL_DIRECTORY}")
VLLM_CONFIG_FILE=$(realpath -- "${VLLM_CONFIG_FILE}")

# The volume syntax uses a colon between host and container paths. Refuse the
# rare ambiguous host path instead of silently mounting something else.
[[ ${MODEL_DIRECTORY} != *:* ]] || die "model directory contains unsupported colon: ${MODEL_DIRECTORY}"
[[ ${VLLM_CONFIG_FILE} != *:* ]] || die "vLLM config path contains unsupported colon: ${VLLM_CONFIG_FILE}"

if [[ -z ${RUNTIME} ]]; then
  if command -v podman > /dev/null; then
    RUNTIME=podman
  elif command -v docker > /dev/null; then
    RUNTIME=docker
  else
    die 'neither podman nor docker was found on PATH'
  fi
fi

case ${RUNTIME} in
  podman)
    command -v podman > /dev/null || die 'podman was not found on PATH'
    GPU_ARGUMENTS=(--device nvidia.com/gpu=all)
    ;;
  docker)
    command -v docker > /dev/null || die 'docker was not found on PATH'
    GPU_ARGUMENTS=(--gpus all)
    ;;
  *) usage_error "unsupported runtime: ${RUNTIME}" ;;
esac

# A private SELinux relabel makes the two bind mounts available to this
# container without disabling SELinux separation. Both mounts remain read-only.
exec "${RUNTIME}" run \
  --rm \
  "${GPU_ARGUMENTS[@]}" \
  --ipc=host \
  --publish 8000:8000 \
  --volume "${MODEL_DIRECTORY}:${CONTAINER_MODEL_DIR}:ro,Z" \
  --volume "${VLLM_CONFIG_FILE}:${CONTAINER_CONFIG_FILE}:ro,Z" \
  --entrypoint vllm \
  "${VLLM_IMAGE}" \
  serve "${CONTAINER_MODEL_DIR}" --config "${CONTAINER_CONFIG_FILE}"

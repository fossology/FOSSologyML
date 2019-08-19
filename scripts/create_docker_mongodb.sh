#!/usr/bin/env bash
# Copyright (C) 2018, Siemens AG
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# SPDX-License-Identifier: GPL-2.0-only

set -e

# script dir
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# project dir
PROJECT_DIR="${SCRIPT_DIR%/*}"

# create dir for mongodb data
mkdir -p ${PROJECT_DIR}/data

# load env variables
source ${PROJECT_DIR}/train_model/.env

# docker entrypoint dir
MONGO_ENTRYPOINT=${PROJECT_DIR}/scripts/mongo-entrypoint/

docker pull mongo:3.6.5

# create container if it doesnt exist
[ ! "$(docker ps -a | grep "mongodb")" ] &&
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v ${MONGO_ENTRYPOINT}:/docker-entrypoint-initdb.d/ \
  -e MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME} \
  -e MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD} \
  -e MONGODB_ADMIN_USERNAME=${MONGODB_ADMIN_USERNAME} \
  -e MONGODB_ADMIN_PASSWORD=${MONGODB_ADMIN_PASSWORD} \
  -e MONGODB_APPLICATION_DATABASE=${MONGODB_APPLICATION_DATABASE} \
  -e MONGODB_APPLICATION_USERNAME=${MONGODB_APPLICATION_USERNAME} \
  -e MONGODB_APPLICATION_PASSWORD=${MONGODB_APPLICATION_PASSWORD} \
  -e MONGO_INITDB_DATABASE=admin \
  mongo:3.6.5
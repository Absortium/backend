    Branch  | Status 
  --------| -------
  master | [![Build Master Status](https://travis-ci.org/absortium/backend.svg?branch=master)](https://travis-ci.org/absortium/backend) 
  development | [![Build Development Status](https://travis-ci.org/absortium/backend.svg?branch=development)](https://travis-ci.org/absortium/backend)


## Getting started  
#### Prerequisites
  
    Name  | Version 
  --------| -------
  docker-compose | 1.8.0-rc1
  docker | 1.12.0-rc3
  
  **Step №1**: Clone repository.  
  ```bash
  $ git clone --recursive https://github.com/absortium/deluge.git
  $ cd deluge
  ```

  **Step №2**: Ask maintainer to give you `.sensitive` file.
  
  **Step №3**: Install `backend` and run tests.
  ```bash
  $ ./useful/install.sh backend
  ```
 
## Hot connect `frontend` to the `backend` and start developing?
  **Step №1**: Install `backend` and tun tests.
  ```bash
  $ ./useful/install.sh frontend
  ```  
  
  **Step №2**: For simplicity I prefer use [aliases](#alias-info) which I developed for this project, on first sign it might look overwhelming, but I think it may significantly help you for developing, so add env variables and aliases from `useful` directory - copy this in the `.bashrc` or `.zshrc` (this code install project aliases every time when you instantiate terminal window):
  ```bash
  export DELUGE_PATH="YOUR_WORK_DIRECTORY_PATH"
  export DEFAULT_MODE="frontend"
  for f in $DELUGE_PATH/useful/aliases/*; do
    source "$f"
  done  
  ```
  
  **Step №3**: Run `frontend`.
  ```bash
  $ dc up frontend
  ```
  
  **Step №4**: Go to the `localhost:3000`
 
## Services
* `m-backend` - main backend service.
* `w-backend` - backend worker service (celery).
* `frontend` - frontend service.
* `postgres` - postgres service (postgres data are stored separately, even if you remove service the data would be persisted).
* `rabbitmq` - queue service.
* `redis` - redis service (needed as backend for `rabbitmq` tasks store).
* `router` - `crossbar.io` service which notify user about new offers, market info, exchange history changes.

## Alias info
* `god` - go to the `DELUGE_PATH` directory.
* `godd` - go to the `docker` dev directory (in order to run docker service)
* `gods` - go to the `services` directory.
* `gods <service>` - go to the `<service>` project directory.
* `dcinit <mode>` - init start mode, default mode is `DEFAULT_MODE` .
    * `unit`
        * external systems like `coinbase` and `ethwallet` are mocked.
        * internal systems like `router` are mocked.
        * generally, only `postgres` service  is required to be up in order to start tests.
        * celery workers are not working and code is executing in main process.
    * `integration`
        * external systems like `coinbase` are mocked.
        * `ethwallet` service might working in private net or might be mocked (it dependence).
        * `postgres`, `rabbitmq`, `celery`, `router` services are required to be up in order to start tests.
        * celery workers are working and celery tasks are executing in another processes.
    * (for more information please read `README.md` in the `docker` directory)         
   
* `dc(b| build) <service>` - build service.
* `dc(r| run) <service>` - run service.
* `drmc <regex>` - delete containers that much regex expression.
* `drmi <regex>` - delete images that much regex expression.
* `dc(l| logs) <service>` - output service logs.
* `di` - list all images.
* `dps` - list all working containers.
* `ideluge` - init sensitive information that is needed for backend start.



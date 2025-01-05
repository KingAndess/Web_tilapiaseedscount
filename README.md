## Setup for Deploy [Flask](https://flask.palletsprojects.com/en/stable/) app with [Gunicorn](https://gunicorn.org/)

1. Update server dependency and install opencv-python, venv, and pip

   ```bash
   sudo apt update && sudo apt upgrade -y && sudo apt install -y python3-opencv python3-venv python3-pip
   ```

2. Clone this project and change to directory

   ```bash
   git clone https://github.com/KingAndess/Web_tilapiaseedscount.git && cd Web_tilapiaseedscount
   ```

3. Create `venv` and activate it

   ```bash
   python3 -m venv venv && source ./venv/bin/activate
   ```

4. Install all packages in `requirements.txt`
   ```bash
   pip install -r requirements.txt
   ```
5. Install [Gunicorn](https://gunicorn.org/)
   ```bash
   pip install gunicorn
   ```
6. Deactivate `venv`
   ```bash
   deactivate
   ```
7. Create service file called `app.servcie` (you can change it).

   ```bash
   sudo nano /etc/systemd/system/app.service
   ```

   paste text below inside `app.service`

   ```conf
    [Unit]
    Description=Gunicorn instance to serve Flask app
    After=network.target

    [Service]
    User=ubuntu
    Group=www-data
    WorkingDirectory=/home/ubuntu/Web_tilapiaseedscount/
    Enveronment="PATH=/home/ubuntu/Web_tilapiaseedscount/venv/bin"
    ExecStart=/home/ubuntu/Web_tilapiaseedscount/venv/bin/gunicorn --workers 3 --bind unix:app.sock wsgi:app

    [Install]
    WantedBy=multi-user.target
   ```

   **Important**: User directory maybe difference so you **should** change it.

8. Exit `app.service` with `ctrl + X` then type `Y` and hit `enter`
9. Run `app.service`

   ```bash
   sudo systemctl start app.service && sudo systemctl enable app.service
   ```

10. For check `app.service` was running, you can use
    ```bash
    sudo systemctl status app.service
    ```
11. Install `nginx` and start it.
    ```bash
    sudo apt install nginx -y && sudo systemctl start nginx && sudo systemctl enable nginx
    ```
12. Backup default config of nginx to backup folder
    ```bash
    mkdir ~/backup && sudo cp /etc/nginx/sites-available/default ~/backup
    ```
13. Replace nginx config code with config code below then save it. (See No. 8 for save file)

    ```
    server {
        listen 80;

        server_name _;

        location / {
            include proxy_params;
            proxy_pass http://unix:/home/ubuntu/Web_tilapiaseedscount/app.sock;
        }
    }
    ```

    **Important**: User directory maybe difference so you **should** change it.

14. Test nginx config
    ```bash
    sudo nginx 0t
    ```
    You will see message. (If not, contact me!)
    ```bash
    nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
    nginx: configuration file /etc/nginx/nginx.conf test is successful
    ```
15. Restart nginx
    ```bash
    sudo systemctl restart nginx
    ```
16. Try access your `public IP Address` your website with `http` protocol. Example `http://<your-ip-addr>`
17. If you get `error 502`, change permission of your `$HOME direcrory`
    ```bash
    sudo chmod 775 /home/<user-directory>
    ```

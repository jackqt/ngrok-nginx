#!/usr/bin/env python
# -*- coding:utf-8 -*-

from subprocess import call
import os
from Runner import Runner

class WinRunner(Runner):
    def __init__(self):
        super(WinRunner, self).__init__()
        self.ngx_dir="../temp"
        self.ngx_bin_file=self.ngx_dir + "/nginx.exe"
        self.ngx_conf_file=self.ngx_dir + "/conf/nginx.conf"

    def check_ngx_installed(self):
        if not os.path.isdir(self.ngx_dir):
            return False
        else:
            p_dir = os.getcwd()
            os.chdir(self.ngx_dir)
            exist_list = [True for d in os.listdir('.') if d.startswith('nginx')]
            os.chdir(p_dir)
            return True in exist_list

    def install_ngx(self):
        print "Prepare to install nginx for windows..."
        def callback(a, b, c):  
            '''回调函数 
            @a: 已经下载的数据块 
            @b: 数据块的大小 
            @c: 远程文件的大小 
            '''  
            per = 100.0 * a * b / c  
            if per > 100:  
                per = 100  
            print 'downloading nginx: %.2f%%' % per

        url="http://nginx.org/download/nginx-1.10.2.zip"
        nginx_name=url.split('/')[-1]
        import urllib
        urllib.urlretrieve(url, nginx_name, callback)
        print "Download nginx complete"
        if os.path.isdir('../temp/'):
            import shutil
            shutil.rmtree('../temp')
        os.makedirs(r'../temp/')

        from zipfile import ZipFile
        zf = ZipFile(nginx_name)
        zf.extractall('../temp/')
        ngx_dir='../temp/'+nginx_name[:-4]
        self.ngx_dir = os.getcwd() + "/" + ngx_dir
        p_dir = os.getcwd()
        os.chdir(ngx_dir)
        print 'Nginx already installed on :', os.getcwd()
        os.chdir(p_dir)
        self.ngx_bin_file=self.ngx_dir + "/nginx.exe"
        self.ngx_conf_file=self.ngx_dir + "/conf/nginx.conf"
        os.remove(nginx_name)

    def config_ngx(self):
        ngx_conf_file="../conf/nginx/nginx.conf.template"
        ngx_sys_file=self.ngx_conf_file
        ngx_port = self.config_parser.get('ngrok_nginx', 'localport')
        backend_host = self.config_parser.get('proxy_backend', 'host')
        backend_port = self.config_parser.get('proxy_backend', 'port')
        frontend_host = self.config_parser.get('proxy_frontend', 'host')
        frontend_port = self.config_parser.get('proxy_frontend', 'port')
        with open(ngx_conf_file, 'r+') as f:
            target_file = open(ngx_sys_file, 'w')
            lines = f.readlines()
            f.seek(0)
            for line in lines:
                if '${NGX_PORT}' in line:
                    line = line.replace('${NGX_PORT}', ngx_port)
                elif '${PROXY_FRONTEND_HOST}' in line:
                    line = line.replace('${PROXY_FRONTEND_HOST}', frontend_host)
                    line = line.replace('${PROXY_FRONTEND_PORT}', frontend_port)
                elif '${PROXY_BACKEND_HOST}' in line:
                    line = line.replace('${PROXY_BACKEND_HOST}', backend_host)
                    line = line.replace('${PROXY_BACKEND_PORT}', backend_port)
                target_file.write(line)
            target_file.close()
            f.close()

        print "Copy nginx file to: ", ngx_sys_file

    def config_ngrok(self):
        # should be config by ngrok.py
        # TODO: config within Runner instead of ngrok.py
        pass

    def check_process_running(self, process_name):
        process_list = os.popen('tasklist').read()
        if process_name not in process_list[:]:
            return False
        else:
            print 'Process: ', process_name, ' is running'
            return True

    def check_ngx_running(self):
        return self.check_process_running("nginx.exe")

    def check_ngrok_running(self):
        return self.check_process_running("ngrok.py")

    def run_command(self, command):
        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        return iter(p.stdout.readline, b'')

    def stop_ngx(self):
        print "Stopping Process: nginx ......"
        newprocess="pkill nginx"
        os.system(newprocess)
        print "Stop Process: nginx - Complete"

    def stop_ngrok(self):
        print "Stop Process: ngrok - Complete"

    def start_ngx(self):
        if self.check_ngx_running():
            self.stop_ngx()
        print "Starting Process: nginx ......"
        import subprocess
        subprocess.Popen(self.ngx_bin_file, shell=True)
        print "Start Process: nginx - Complete"

    def start_ngrok(self):
        if self.check_ngrok_running():
            self.stop_ngrok()
        print "Starting Process: ngrok ......"
        print "Start Process: ngrok - Complete", "\n"
        newprocess="nohup python ngrok.py &"
        os.system(newprocess)

    def get_ngx_port(self):
        return self.config_parser.get('ngrok_nginx', 'localport')

    def get_ngrok_domain(self):
        host = self.config_parser.get('ngrok', 'host')
        subdomain = self.config_parser.get('ngrok_nginx', 'subdomain')
        return subdomain + "." + host

    def config(self):
        if not self.check_ngx_installed():
            self.install_ngx()
        self.config_ngx()
        self.config_ngrok()

    def run(self):
        self.start_ngx()
        self.start_ngrok()

        print "Nginx already started on port: ", self.get_ngx_port()



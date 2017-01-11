#!/usr/bin/env python
# -*- coding:utf-8 -*-

from subprocess import call
import os
from Runner import Runner

class MacRunner(Runner):
    def __init__(self):
        super(MacRunner, self).__init__()
        self.ngx_bin_file="/usr/local/bin/nginx"

    def check_ngx_installed(self):
        return os.path.isfile(self.ngx_bin_file)

    def install_ngx(self):
        call("brew", "install", "nginx")

    def config_ngx(self):
        ngx_conf_file="../conf/nginx/nginx.conf.template"
        ngx_sys_file="../conf/nginx/nginx.conf"
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
        process_list = os.popen("ps -Af").read()
        if process_name not in process_list[:]:
            return False
        else:
            print 'Process: ', process_name, ' is running'
            return True

    def check_ngx_running(self):
        return self.check_process_running("nginx")

    def check_ngrok_running(self):
        return self.check_process_running("ngrok")

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
        import subprocess
        ngrok_process="ps -ef|grep ngrok|grep -v grep|awk '{print $2}'"
        temp = subprocess.Popen(ngrok_process, stdout=subprocess.PIPE, shell=True)
        (output, err) = temp.communicate()
        if not output == None:
            ngrok_id_list = output.split("\n")
            for ngrok_id in ngrok_id_list:
                if ngrok_id == '':
                    continue
                newprocess = "kill " + ngrok_id
                os.system(newprocess)
        print "Stop Process: ngrok - Complete"

    def start_ngx(self):
        if self.check_ngx_running():
            self.stop_ngx()
        print "Starting Process: nginx ......"
        call(self.ngx_bin_file)
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
        print "Ngrok already started on domain: ", self.get_ngrok_domain()

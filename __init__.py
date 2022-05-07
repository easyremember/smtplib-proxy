import ssl
import socket
from smtplib import SMTP, SMTP_SSL
import socks

##### Reference #############
# https://github.com/python/cpython/blob/3.7/Lib/smtplib.py
# https://github.com/Anorov/PySocks/blob/master/socks.py

# Proxy parameters (refer to set_proxy() method of socks.socksocket):
#   - proxy_type: only SOCKS5 (PROXY_TYPE_SOCKS5) is supported by this helper
#   - addr
#   - port
#   - rdns: not used
#   - username
#   - password

# This is a helper class to send mail via SMTP protocol. 
# Only TLS or SSL connection is supported.
class SMTPPROXY(object):
    def __init__(self, smtp_host, smtp_port, user=None, password=None, encrypt_mode=None, timeout=5, proxy=None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.user = user
        self.password = password
        self.encrypt_mode = None if encrypt_mode is None else encrypt_mode.upper()
        if self.encrypt_mode is not None:
            if self.encrypt_mode != 'TLS' and self.encrypt_mode != 'SSL':
                raise Exception(f"Invalid encrypt_mode ({encrypt_mode}), only SSL or TLS is supported ")
        self.timeout = timeout
        if proxy is not None and 'proxy_type' not in proxy:
            proxy['proxy_type'] = socks.PROXY_TYPE_SOCKS5
        self.proxy = proxy
        self.server = None
        self._connect()
        
    def _connect(self):
        if self.encrypt_mode == 'SSL':
            # Create a SSL context
            context = ssl.create_default_context()
            self.server = _SMTP_SSL_PROXY_WRAPPER(self.smtp_host, self.smtp_port, context=context, timeout=self.timeout, proxy=self.proxy)
        else: ## 'TLS' or None
            self.server = _SMTP_PROXY_WRAPPER(self.smtp_host, self.smtp_port, timeout=self.timeout, proxy=self.proxy)
            if self.encrypt_mode == 'TLS':
                self.server.starttls()
        
        if self.user is not None and self.password is not None:
            self.server.login(self.user, self.password) 

    def send(self, from_address, to_addresses, message, auto_retry=True):
        try:
            self.server.sendmail(from_address, to_addresses, message)
        except Exception:
            if auto_retry:
                self._connect()
                self.server.sendmail(from_address, to_addresses, message)
            else:
                raise

    def close(self):
        if self.server is not None:
            self.server.close()
            self.server = None

    def __del__(self):
        if self.server is not None:
            self.server.close()

class _SMTP_PROXY_WRAPPER(SMTP):
    def __init__(self, host='', port=0, local_hostname=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=None, proxy=None):
        self.proxy = proxy
        super(_SMTP_PROXY_WRAPPER, self).__init__(host, port, local_hostname, timeout, source_address)
    
    def _get_socket(self, host, port, timeout):
        if self.proxy is None:
            # use the orignal way to get the socket
            return super(_SMTP_PROXY_WRAPPER, self)._get_socket(host, port, timeout)
        else:
            #use socksocket for proxy connection handling
            proxy_sock = socks.socksocket()
            proxy_sock.set_proxy(**self.proxy)
            if isinstance(timeout, (int, float)):
                proxy_sock.settimeout(timeout)
            proxy_sock.connect((host, port))
            return proxy_sock

class _SMTP_SSL_PROXY_WRAPPER(SMTP_SSL):
    def __init__(self, host='', port=0, local_hostname=None,
                     keyfile=None, certfile=None,
                     timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                     source_address=None, context=None, proxy=None):
        self.proxy = proxy
        super(_SMTP_SSL_PROXY_WRAPPER, self).__init__(host, port, local_hostname, keyfile, certfile, timeout, source_address, context)

    def _get_socket(self, host, port, timeout):
        if self.proxy is None:
            # use the orignal way to get the socket
            return super(_SMTP_SSL_PROXY_WRAPPER, self)._get_socket(host, port, timeout)
        else:
            #use socksocket for proxy connection handling
            proxy_sock = socks.socksocket()
            proxy_sock.set_proxy(**self.proxy)
            if isinstance(timeout, (int, float)):
                proxy_sock.settimeout(timeout)
            proxy_sock.connect((host, port))
            new_socket = self.context.wrap_socket(proxy_sock, server_hostname=self._host)
            return new_socket

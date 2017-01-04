import errno
import re
import socket
import ssl
import threading
import time


class IRCClient(object):
    def __init__(self,
                 server='127.0.0.1',
                 port=6667,
                 ssl=True,
                 encoding='utf-8',
                 nick='yetanotherbot',
                 user=None,
                 password=None,
                 realname='',
                 timeout=120):
        self.socket = None
        self.quitting = False

        self.server = server
        self.port = port
        self.ssl = ssl
        self.encoding = encoding
        self.nick = nick
        self.user = user
        self.password = password
        self.realname = realname
        self.timeout = timeout

    # send a raw line to the server
    def send_raw(self, msg):
        try:
            # strip newlines
            bad_chars = '\r\n'
            # TODO: compile regex
            stripped = re.sub('[' + bad_chars + ']+', '', msg)

            # clamp length
            if len(stripped) > 400:
                stripped = stripped[:400]

            stripped += '\r\n'
            utf8 = stripped.encode(self.encoding)

            self.socket.send(utf8)

        except TypeError as ex:
            return False  # invalid msg
        except Exception as ex:
            # something else went horribly wrong, disconnect

            self.on_log('Exception while sending data: %s' % repr(ex))
            self.disconnect()
        return True

    # send a message to a channel/user
    def send_privmsg(self, channel, msg):
        if not channel or not msg:
            return
        self.send_raw('PRIVMSG %s :%s' % (channel, msg))

    # set the nick
    def set_nick(self, nick):
        self.send_raw('NICK %s' % nick)

    # join a channel
    def join(self, channel):
        self.send_raw('JOIN %s' % channel)

    # leave a channel
    def part(self, channel):
        self.send_raw('PART %s' % channel)

    # quit from the server
    # also ends the main loop gracefully
    def quit(self, reason):
        self.send_raw('QUIT :%s' % reason)
        self.quitting = True

    # parse a message received from the server and split it into manageable parts
    # *inspired by* twisted's irc implementation
    def parse_server_cmd(self, cmd):
        prefix = ''
        trailing = []
        if not cmd:
            return None
        try:
            if cmd[0] == ':':
                prefix, cmd = cmd[1:].split(' ', 1)
            if cmd.find(' :') != -1:
                cmd, trailing = cmd.split(' :', 1)
                args = cmd.split()
                args.append(trailing)
            else:
                args = cmd.split()
            cmd = args.pop(0)
            return prefix, cmd, args
        except Exception as ex:
            self.on_log('Received invalid message from server: %s' % cmd)
            return None, None, None

    # handle a received command (that has been parsed by parseServerCmd())
    def handle_server_cmd(self, prefix, cmd, args):
        handler = getattr(self, 'cmd_%s' % cmd, None)
        if handler:
            handler(prefix, args)

    def nick_from_prefix(self, prefix):
        return prefix.split('!')[0]

    def cmd_NICK(self, prefix, args):
        nick = self.nick_from_prefix(prefix)
        if nick == self.nick:
            self.nick = nick
        self.on_nick(nick, args[0])

    def cmd_PING(self, prefix, args):
        self.send_raw('PONG :%s' % args[0])

    def cmd_PRIVMSG(self, prefix, args):
        self.on_privmsg(self.nick_from_prefix(prefix), args[0], args[1])

    def cmd_ERROR(self, prefix, args):
        self.on_error(args[0])
        self.disconnect()

    # ErrNickNameInUse
    def cmd_433(self, prefix, args):
        self.nick = args[1] + '_'
        self.set_nick(self.nick)

    # ErrNoMotd
    def cmd_422(self, prefix, args):
        self.on_serverready()

    # EndOfMotd
    def cmd_376(self, prefix, args):
        self.on_serverready()

    def on_nick(self, old, new):
        pass

    def on_part(self, nick, channel):
        pass

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_serverready(self):
        pass

    def on_privmsg(self, nick, target, msg):
        pass

    def on_rawmsg(self, msg):
        """raw data from the server"""
        pass

    def on_error(self, error):
        pass

    # try to connect to a server
    # TODO: handle failed self.send_raw calls somehow?
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # enable ssl
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)
        try:
            self.socket.connect((self.server, self.port))
            self.socket.setblocking(False)

            if self.password:
                self.send_raw('PASS %s' % self.password)

            self.set_nick(self.nick)
            if self.user:
                self.send_raw('USER %s 0 * :%s' % (self.user, self.realname))
        except Exception as ex:
            self.on_log('Connecting failed: %s' % repr(ex))
            return False

        self.on_connect()
        return True

    # close the socket
    def disconnect(self):
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.on_disconnect()
            return True
        return False

    # main loop
    def run(self):
        while not self.quitting:
            # try connecting indefinitely
            while not self.connect():
                time.sleep(30)

            # main recv loop
            recv = ''
            last_time = time.time()  # timestamp for detecting timeouts
            sent_ping = False
            while not self.quitting:
                try:
                    now = time.time()
                    diff = now - last_time

                    # send a ping at half the timeout
                    if diff > self.timeout/2.0 and not sent_ping:
                        self.send_raw('PING :%s' % self.nick)
                        sent_ping = True

                    # no messages received after timeout, try to reconnect
                    if diff > self.timeout:
                        break

                    recv += self.socket.recv(4098).decode(self.encoding)

                    last_time = now
                    sent_ping = False
                except socket.error as e:
                    err = e.args[0]
                    # sleep for a short time, if no data was received
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK or err == errno.ENOENT:
                        time.sleep(0.1)
                        continue
                except Exception as ex:
                    self.on_log('Exception occurred receiving data: %s' % repr(ex))
                    break  # break inner loop, try to reconnect

                # split received data into messages and process them
                while '\r\n' in recv:
                    line, recv = recv.split('\r\n', 1)
                    self.on_rawmsg(line)
                    prefix, cmd, args = self.parse_server_cmd(line)
                    if cmd:
                        self.handle_server_cmd(prefix, cmd, args)

            self.disconnect()

        return True

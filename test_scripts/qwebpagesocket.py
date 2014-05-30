class QTimerWithPause(QTimer):

    def __init__(self, parent = None):

        super(QTimerWithPause, self).__init__ (parent)

        self.startTime = 0
        self.interval  = 0

        return

    def start(self, interval):

        from time import time

        self.interval  = interval
        self.startTime = time()

        super(QTimerWithPause, self).start(interval)

        return

    def pause(self):

        from time import time

        if self.isActive ():

            self.stop()

            elapsedTime = self.startTime - time()
            self.startTime -= elapsedTime

            # time() returns float secs, interval is int msec
            self.interval -= int(elapsedTime*1000)+1

        return

    def resume(self):

        if not self.isActive():
            self.start(self.interval)

        return


class CrawlerWebServer(QWebView):  

    TIMEOUT = 60
    STUPID  = r"(bing|yahoo|google)"

    def __init__(self, host="0.0.0.0", port=50007, parent=None, enableImages=True, enablePlugins=True):

        # Constructor

        super(CrawlerWebServer, self).__init__(parent)  

        self.command     = None
        self.isLoading   = True
        self.isConnected = False
        self.url         = QUrl("http://mast3rpee.tk/")
        self.timeout     = QTimerWithPause(self)
        self.socket      = QTcpServer(self)


        # 1: Settings

        self.settings().enablePersistentStorage()
        self.settings().setAttribute(QWebSettings.AutoLoadImages, enableImages)
        self.settings().setAttribute(QWebSettings.PluginsEnabled, enablePlugins)
        self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)

        # 2: Server
        if args.verbosity > 0: print "Starting server..."

        self.socket.setProxy(QNetworkProxy(QNetworkProxy.NoProxy))
        self.socket.listen(QHostAddress(host), int(port))
        self.connect(self.socket, SIGNAL("newConnection()"), self._connect)

        if args.verbosity > 1:
            print "    Waiting for connection(" + host + ":" + str(port) + ")..."

        # 3: Default page

        self._load(10*1000, self._loadFinished)

        return

    def __del__(self):

        try:
            self.conn.close()
            self.socket.close()
        except:
            pass

        return

    def _sendAuth(self):

        self.conn.write("Welcome to WebCrawler server (http://mast3rpee.tk)\r\n\rLicenced under GPL\r\n\r\n")

    def _connect(self): 

        self.disconnect(self.socket, SIGNAL("newConnection()"), self._connect)

        self.conn               = self.socket.nextPendingConnection()
        self.conn.nextBlockSize = 0

        self.connect(self.conn, SIGNAL("readyRead()"), self.io)
        self.connect(self.conn, SIGNAL("disconnected()"), self.close)
        self.connect(self.conn, SIGNAL("error()"), self.close)
        self._sendAuth()

        if args.verbosity > 1:
            print "    Connection by:", self.conn.peerAddress().toString()

        self.isConnected = True

        if self.isLoading == False:
            self.conn.write("\r\nEnter command:")

        return

    def io(self):

        if self.isLoading: return None

        if args.verbosity > 0:
            print "Reading command..."

        data = self.conn.read(1024).strip(" \r\n\t")

        if not data: return None

        elif self.command is not None:
            r = self.command(data)
            self.command = None
            return r

        return self._getCommand(data)

    def _getCommand(self, d):

        from re import search

        d = unicode(d, errors="ignore")

        if search(r"(help|HELP)", d) is not None:

            self.conn.write("URL | JS | WAIT | QUIT\r\n\r\nEnter Command:")

        elif search(r"(url|URL)", d) is not None:

            self.command = self._print

            self.conn.write("Enter address:")

        elif search(r"(js|JS|javascript|JAVASCRIPT)", d) is not None:

            self.command = self._js

            self.conn.write("Enter javascript to execte:")

        elif search(r"(wait|WAIT)", d) is not None:

            self.loadFinished.connect(self._loadFinishedPrint)
            self.loadFinished.connect(self._loadFinished)  

        elif search(r"(quit|QUIT|exit|EXIT)", d) is not None:

            self.close()

        else:

            self.conn.write("Invalid command!\r\n\r\nEnter Command:")

        return

    def _print(self, d):

        u = d[:250]

        self.out(u)

        return True

    def _js(self, d):

        try:
            self.page().mainFrame().evaluateJavaScript(d)

        except:
            pass

        self.conn.write("Enter Javascript:")

        return True

    def _stop(self):

        from time import sleep

        if self.isLoading == False: return

        if args.verbosity > 0:
            print "    Stopping..."

        self.timeout.stop()
        self.stop()

    def _load(self, timeout, after):

        # Loads a page into frame / sets up timeout

        self.timeout.timeout.connect(self._stop)
        self.timeout.start(timeout)

        self.loadFinished.connect(after)  
        self.load(self.url)

        return

    def _loadDone(self, disconnect = None):

        from re   import search
        from time import sleep

        self.timeout.timeout.disconnect(self._stop)
        self.timeout.stop()

        if disconnect is not None:

            self.loadFinished.disconnect(disconnect)

            # Stick a while on the page

            if search(CrawlerWebServer.STUPID, self.url.toString(QUrl.RemovePath)) is not None:
                sleep(5)
            else:
                sleep(1)

        return

    def _loadError(self):

        from time import sleep, time

        if not self.timeout.isActive(): return True

        if args.verbosity > 0: print "    Error retrying..."

        # 1: Pause timeout

        self.timeout.pause()

        # 2: Check for internet connection

        while self.page().networkAccessManager().networkAccessible() == QNetworkAccessManager.NotAccessible: sleep(1)

        # 3: Wait then try again

        sleep(2)
        self.reload()
        self.timeout.resume()

        return False

    def go(self, url, after = None):

        # Go to a specific address

        global args

        if after is None:
            after = self._loadFinished

        if args.verbosity > 0:
            print "Loading url..."

        self.url        = QUrl(url)
        self.isLoading  = True

        if args.verbosity > 1:
            print "   ", self.url.toString()

        self._load(CrawlerWebServer.TIMEOUT * 1000, after)

        return

    def out(self, url):

        # Print html of a a specific url

        self.go(url, self._loadFinishedPrint)

        return

    def createWindow(self, windowType):  

        # Load links in the same web-view.

        return self  

    def _loadFinished(self, ok):

        # Default LoadFinished

        from time import sleep
        from re   import search

        if self.isLoading == False: return

        if ok == False:
            if not self._loadError(): return 

        self._loadDone(self._loadFinished)

        if args.verbosity > 1:
            print "    Done"

        if self.isConnected == True:
            self.conn.write("\r\nEnter command:")

        self.isLoading = False

        return

    def _loadFinishedPrint(self, ok):  

        # Print the evaluated HTML to stdout

        if self.isLoading == False: return

        if ok == False:
            if not self._loadError(): return 

        self._loadDone(self._loadFinishedPrint)  

        if args.verbosity > 1:
            print "    Done"

        h = unicode( self.page().mainFrame().toHtml(), errors="ignore" )

        if args.verbosity > 2:
            print "------------------\n" + h + "\n--------------------"

        self.conn.write(h)
        self.conn.write("\r\nEnter command:")

        self.isLoading  = False

        return

    def contextMenuEvent(self, event):  

        # Context Menu

        menu = self.page().createStandardContextMenu()  
        menu.addSeparator()  
        action = menu.addAction('ReLoad')  

        @action.triggered.connect  
        def refresh():  
            self.load(self.url)

        menu.exec_(QCursor.pos())


class CrawlerWebClient(object):

    def __init__(self, host, port):

        import socket

        global args

        # CONNECT TO SERVER

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((host, port))

        o = self.read()

        if args.verbosity > 2:
            print "\n------------------------------\n" + o + "\n------------------------------\n"

        return

    def __del__(self):

        try: self.socket.close()
        except: pass

    def read(self):

        from re import search

        r = ""

        while True:
            out = self.socket.recv(64*1024).strip("\r\n")

            if out.startswith(r"Enter"):
                break

            if out.endswith(r"Enter command:"):
                r += out[:-14]
                break

            r += out

        return r

    def command(self, command):

        global args

        if args.verbosity > 2:
            print "    Command: [" + command + "]\n------------------------------"

        self.socket.sendall(unicode(command))

        r =  self.read()

        if args.verbosity > 2:
            print r, "\n------------------------------\n"

        return r

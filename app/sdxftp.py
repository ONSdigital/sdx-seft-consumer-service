import io
import zipfile
from ftplib import FTP


class SDXFTP(object):

    def __init__(self, logger, host, user, passwd, port=21):
        self._conn = None
        self.host = host
        self.user = user
        self.passwd = passwd
        self.logger = logger
        self.port = port
        return

    def get_connection(self):
        """Connect checks whether an ftp connection is already open and, if
        not, attempts to open a new one.
        """
        if self._conn is None:
            # No connection at all
            self.logger.info("Establishing new FTP connection", host=self.host)
            return self._connect()
        else:
            try:
                self._conn.voidcmd("NOOP")
            except IOError:
                # Bad response so assume connection is dead and attempt
                # to reopen.
                self.logger.info("FTP connection no longer alive, re-establishing connection", host=self.host)
                return self._connect()

            # Connection exists and seems healthy
            self.logger.info("FTP connection already established", host=self.host)
            return self._conn

    def _connect(self):
        self._conn = FTP()
        self._conn.connect(self.host, self.port)
        self._conn.login(user=self.user, passwd=self.passwd)
        return self._conn

    def deliver_binary(self, folder, filename, data):
        """Delivery binary delivers a single binary file to the given folder
        """
        self.logger.info("Delivering binary file to FTP", host=self.host, folder=folder, filename=filename)
        stream = io.BytesIO(data)
        conn = self.get_connection()
        conn.cwd(folder)
        conn.storbinary('STOR ' + filename, stream)
        self.logger.info("Delivered binary file to FTP", host=self.host, folder=folder, filename=filename)

    def unzip_and_deliver(self, folder, zip_contents):
        """Unzip and deliver processes a zip file and delivers the unzipped
        contents to the given folder.
        """
        try:
            z = zipfile.ZipFile(io.BytesIO(zip_contents))

            for filename in z.namelist():
                if filename.endswith('/'):
                    continue

                edc_file = z.open(filename)
                self.deliver_binary(folder, filename, edc_file.read())

            self.logger.info("Successfully delivered zip to FTP", host=self.host)
            return True

        except (RuntimeError, zipfile.BadZipfile) as e:
            self.logger.error("Failed to deliver zip to FTP", host=self.host, error=e)
            return False

import binascii
import io
import os
import struct
import sys
import time

try:
    import stat
except ImportError:
    pass

class UnsupportedOperation(OSError):
    pass

# --- MicroPython Shims ---
class BufferedIOBase:
    def __init__(self):
        self.closed = False
    def close(self):
        self.closed = True
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.close()
    def readline(self, limit=-1):
        return self.read(limit)

class RLock:
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        pass

def copyfileobj(fsrc, fdst, length=0):
    if not length:
        length = 1 * 1024
    while True:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)

def os_stat(path):
    return os.stat(path)

def path_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False

def makedirs(path):
    parts = path.split('/')
    p = ""
    for part in parts:
        if not part: continue
        p += part + "/"
        try:
            os.mkdir(p)
        except OSError:
            pass

class BadZipFile(Exception):
    pass

class LargeZipFile(Exception):
    pass

error = BadZipFile

ZIP_STORED = 0
ZIP_DEFLATED = 8
ZIP_BZIP2 = 12
ZIP_LZMA = 14

structEndArchive = b"<4s4H2LH"
stringEndArchive = b"PK\005\006"
sizeEndCentDir = struct.calcsize(structEndArchive)

_ECD_SIGNATURE = 0
_ECD_DISK_NUMBER = 1
_ECD_DISK_START = 2
_ECD_ENTRIES_THIS_DISK = 3
_ECD_ENTRIES_TOTAL = 4
_ECD_SIZE = 5
_ECD_OFFSET = 6
_ECD_COMMENT_SIZE = 7
_ECD_COMMENT = 8
_ECD_LOCATION = 9

structCentralDir = "<4s4B4HL2L5H2L"
stringCentralDir = b"PK\001\002"
sizeCentralDir = struct.calcsize(structCentralDir)

_CD_SIGNATURE = 0
_CD_FLAG_BITS = 5
_CD_COMPRESS_TYPE = 6
_CD_FILENAME_LENGTH = 12
_CD_EXTRA_FIELD_LENGTH = 13
_CD_COMMENT_LENGTH = 14
_CD_LOCAL_HEADER_OFFSET = 18

_MASK_ENCRYPTED = 1 << 0
_MASK_USE_DATA_DESCRIPTOR = 1 << 3
_MASK_UTF_FILENAME = 1 << 11

structFileHeader = "<4s2B4HL2L2H"
stringFileHeader = b"PK\003\004"
sizeFileHeader = struct.calcsize(structFileHeader)

_FH_SIGNATURE = 0
_FH_GENERAL_PURPOSE_FLAG_BITS = 3
_FH_COMPRESSION_METHOD = 4
_FH_FILENAME_LENGTH = 10
_FH_EXTRA_FIELD_LENGTH = 11

structEndArchive64Locator = "<4sLQL"
stringEndArchive64Locator = b"PK\x06\x07"
sizeEndCentDir64Locator = struct.calcsize(structEndArchive64Locator)

structEndArchive64 = "<4sQ2H2L4Q"
stringEndArchive64 = b"PK\x06\x06"
sizeEndCentDir64 = struct.calcsize(structEndArchive64)

try:
    import zlib
    crc32 = zlib.crc32
except ImportError:
    zlib = None
    crc32 = binascii.crc32

try:
    import deflate
except ImportError:
    deflate = None

def _check_zipfile(fp):
    try:
        if _EndRecData(fp):
            return True
    except OSError:
        pass
    return False

def is_zipfile(filename):
    result = False
    try:
        if hasattr(filename, "read"):
            result = _check_zipfile(fp=filename)
        else:
            with open(filename, "rb") as fp:
                result = _check_zipfile(fp)
    except OSError:
        pass
    return result

def _EndRecData64(fpin, offset, endrec):
    try:
        fpin.seek(offset - sizeEndCentDir64Locator, 2)
    except OSError:
        return endrec
    data = fpin.read(sizeEndCentDir64Locator)
    if len(data) != sizeEndCentDir64Locator:
        return endrec
    sig, diskno, reloff, disks = struct.unpack(structEndArchive64Locator, data)
    if sig != stringEndArchive64Locator:
        return endrec
    if diskno != 0 or disks > 1:
        raise BadZipFile("zipfiles that span multiple disks are not supported")
    fpin.seek(offset - sizeEndCentDir64Locator - sizeEndCentDir64, 2)
    data = fpin.read(sizeEndCentDir64)
    if len(data) != sizeEndCentDir64:
        return endrec
    sig, sz, create_version, read_version, disk_num, disk_dir, \
        dircount, dircount2, dirsize, diroffset = \
        struct.unpack(structEndArchive64, data)
    if sig != stringEndArchive64:
        return endrec
    endrec[_ECD_SIGNATURE] = sig
    endrec[_ECD_DISK_NUMBER] = disk_num
    endrec[_ECD_DISK_START] = disk_dir
    endrec[_ECD_ENTRIES_THIS_DISK] = dircount
    endrec[_ECD_ENTRIES_TOTAL] = dircount2
    endrec[_ECD_SIZE] = dirsize
    endrec[_ECD_OFFSET] = diroffset
    return endrec

def _EndRecData(fpin):
    fpin.seek(0, 2)
    filesize = fpin.tell()
    try:
        fpin.seek(-sizeEndCentDir, 2)
    except OSError:
        return None
    data = fpin.read()
    if (len(data) == sizeEndCentDir and
        data[0:4] == stringEndArchive and
        data[-2:] == b"\000\000"):
        endrec = list(struct.unpack(structEndArchive, data))
        endrec.append(b"")
        endrec.append(filesize - sizeEndCentDir)
        return _EndRecData64(fpin, -sizeEndCentDir, endrec)
    maxCommentStart = max(filesize - (1 << 16) - sizeEndCentDir, 0)
    fpin.seek(maxCommentStart, 0)
    data = fpin.read()
    start = data.rfind(stringEndArchive)
    if start >= 0:
        recData = data[start:start+sizeEndCentDir]
        if len(recData) != sizeEndCentDir:
            return None
        endrec = list(struct.unpack(structEndArchive, recData))
        commentSize = endrec[_ECD_COMMENT_SIZE]
        comment = data[start+sizeEndCentDir:start+sizeEndCentDir+commentSize]
        endrec.append(comment)
        endrec.append(maxCommentStart + start)
        return _EndRecData64(fpin, maxCommentStart + start - filesize, endrec)
    return None

def _sanitize_filename(filename):
    null_byte = filename.find(chr(0))
    if null_byte >= 0:
        filename = filename[0:null_byte]
    filename = filename.replace('\\', '/')
    return filename

class ZipInfo:
    __slots__ = (
        'orig_filename', 'filename', 'date_time', 'compress_type',
        'comment', 'extra', 'create_system', 'create_version',
        'extract_version', 'reserved', 'flag_bits', 'volume',
        'internal_attr', 'external_attr', 'header_offset',
        'CRC', 'compress_size', 'file_size', '_raw_time',
        '_end_offset'
    )

    def __init__(self, filename="NoName", date_time=(1980,1,1,0,0,0)):
        self.orig_filename = filename
        self.filename = _sanitize_filename(filename)
        self.date_time = date_time
        self.compress_type = ZIP_STORED
        self.comment = b""
        self.extra = b""
        self.create_system = 0
        self.create_version = 20
        self.extract_version = 20
        self.reserved = 0
        self.flag_bits = 0
        self.volume = 0
        self.internal_attr = 0
        self.external_attr = 0
        self.compress_size = 0
        self.file_size = 0
        self._end_offset = None
        self.header_offset = 0
        self.CRC = 0

    def is_dir(self):
        return self.filename.endswith('/')

    def _encodeFilenameFlags(self):
        try:
            return self.filename.encode('ascii'), self.flag_bits
        except UnicodeEncodeError:
            return self.filename.encode('utf-8'), self.flag_bits | _MASK_UTF_FILENAME

    def _decodeExtra(self, filename_crc):
        extra = self.extra
        unpack = struct.unpack
        while len(extra) >= 4:
            tp, ln = unpack('<HH', extra[:4])
            if ln+4 > len(extra):
                break
            if tp == 0x0001:
                data = extra[4:ln+4]
                try:
                    if self.file_size in (0xFFFF_FFFF_FFFF_FFFF, 0xFFFF_FFFF):
                        self.file_size, = unpack('<Q', data[:8])
                        data = data[8:]
                    if self.compress_size == 0xFFFF_FFFF:
                        self.compress_size, = unpack('<Q', data[:8])
                        data = data[8:]
                    if self.header_offset == 0xFFFF_FFFF:
                        self.header_offset, = unpack('<Q', data[:8])
                except Exception:
                    pass
            elif tp == 0x7075:
                data = extra[4:ln+4]
                try:
                    up_version, up_name_crc = unpack('<BL', data[:5])
                    if up_version == 1 and up_name_crc == filename_crc:
                        up_unicode_name = data[5:].decode('utf-8')
                        if up_unicode_name:
                            self.filename = _sanitize_filename(up_unicode_name)
                except Exception:
                    pass
            extra = extra[ln+4:]

_crctable = None
def _gen_crc(crc):
    for j in range(8):
        if crc & 1:
            crc = (crc >> 1) ^ 0xEDB88320
        else:
            crc >>= 1
    return crc

def _ZipDecrypter(pwd):
    key0 = 305419896
    key1 = 591751049
    key2 = 878082192
    global _crctable
    if _crctable is None:
        _crctable = list(map(_gen_crc, range(256)))
    crctable = _crctable
    def crc32(ch, crc):
        return (crc >> 8) ^ crctable[(crc ^ ch) & 0xFF]
    def update_keys(c):
        nonlocal key0, key1, key2
        key0 = crc32(c, key0)
        key1 = (key1 + (key0 & 0xFF)) & 0xFFFFFFFF
        key1 = (key1 * 134775813 + 1) & 0xFFFFFFFF
        key2 = crc32(key1 >> 24, key2)
    for p in pwd:
        update_keys(p)
    def decrypter(data):
        result = bytearray()
        append = result.append
        for c in data:
            k = key2 | 2
            c ^= ((k * (k^1)) >> 8) & 0xFF
            update_keys(c)
            append(c)
        return bytes(result)
    return decrypter

class DeflateDecompressor:
    def __init__(self):
        self._decomp = None
        self.unconsumed_tail = b''
        self.eof = False
    def decompress(self, data, max_length=0):
        if not data: return b''
        stream = io.BytesIO(data)
        try:
            with deflate.DeflateIO(stream, deflate.AUTO) as d:
                decompressed = d.read()
        except Exception:
            return b''
        return decompressed
    def flush(self):
        return b''

def _get_decompressor(compress_type):
    if compress_type == ZIP_STORED:
        return None
    elif compress_type == ZIP_DEFLATED:
        if deflate:
            return DeflateDecompressor()
        else:
            return zlib.decompressobj(-15)
    else:
        raise NotImplementedError("compression type %d" % compress_type)

class _SharedFile:
    def __init__(self, file, pos, close, lock):
        self._file = file
        self._pos = pos
        self._close = close
        self._lock = lock
    def seekable(self):
        return hasattr(self._file, 'seek')
    def tell(self):
        return self._pos
    def seek(self, offset, whence=0):
        with self._lock:
            self._file.seek(offset, whence)
            self._pos = self._file.tell()
            return self._pos
    def read(self, n=-1):
        with self._lock:
            self._file.seek(self._pos)
            data = self._file.read(n)
            self._pos = self._file.tell()
            return data
    def close(self):
        if self._file is not None:
            fileobj = self._file
            self._file = None
            self._close(fileobj)

class ZipExtFile(BufferedIOBase):
    MAX_N = 1 << 31 - 1
    MIN_READ_SIZE = 4096
    MAX_SEEK_READ = 1 << 24

    def __init__(self, fileobj, zipinfo, pwd=None, close_fileobj=False):
        super().__init__()
        self._fileobj = fileobj
        self._pwd = pwd
        self._close_fileobj = close_fileobj
        self._compress_type = zipinfo.compress_type
        self._compress_left = zipinfo.compress_size
        self._left = zipinfo.file_size
        self._decompressor = _get_decompressor(self._compress_type)
        self._eof = False
        self._readbuffer = b''
        self._offset = 0
        self.name = zipinfo.filename
        self._expected_crc = zipinfo.CRC
        self._running_crc = crc32(b'')
        self._decrypter = None
        if pwd:
            check_byte = (zipinfo.CRC >> 24) & 0xff
            if (zipinfo.flag_bits & _MASK_USE_DATA_DESCRIPTOR):
                check_byte = (zipinfo._raw_time >> 8) & 0xff
            h = self._init_decrypter()
            if h != check_byte:
                raise RuntimeError("Bad password")

    def _init_decrypter(self):
        self._decrypter = _ZipDecrypter(self._pwd)
        header = self._fileobj.read(12)
        self._compress_left -= 12
        return self._decrypter(header)[11]

    def read(self, n=-1):
        if n is None or n < 0:
            buf = self._readbuffer[self._offset:]
            self._readbuffer = b''
            self._offset = 0
            while not self._eof:
                buf += self._read1(self.MAX_N)
            return buf
        end = n + self._offset
        if end < len(self._readbuffer):
            buf = self._readbuffer[self._offset:end]
            self._offset = end
            return buf
        n = end - len(self._readbuffer)
        buf = self._readbuffer[self._offset:]
        self._readbuffer = b''
        self._offset = 0
        while n > 0 and not self._eof:
            data = self._read1(n)
            if n < len(data):
                self._readbuffer = data
                self._offset = n
                buf += data[:n]
                break
            buf += data
            n -= len(data)
        return buf

    def _update_crc(self, newdata):
        self._running_crc = crc32(newdata, self._running_crc)
        if self._eof and self._running_crc != self._expected_crc:
            raise BadZipFile("Bad CRC-32")

    def _read1(self, n):
        if self._eof or n <= 0: return b''
        data = self._read2(n)
        if self._compress_type == ZIP_STORED:
            self._eof = self._compress_left <= 0
        elif self._compress_type == ZIP_DEFLATED and zlib:
            n = max(n, self.MIN_READ_SIZE)
            data = self._decompressor.decompress(data, n)
            self._eof = (self._decompressor.eof or self._compress_left <= 0 and not self._decompressor.unconsumed_tail)
            if self._eof: data += self._decompressor.flush()
        else:
            data = self._decompressor.decompress(data)
            self._eof = self._decompressor.eof or self._compress_left <= 0
        data = data[:self._left]
        self._left -= len(data)
        if self._left <= 0: self._eof = True
        self._update_crc(data)
        return data

    def _read2(self, n):
        if self._compress_left <= 0: return b''
        n = max(n, self.MIN_READ_SIZE)
        n = min(n, self._compress_left)
        data = self._fileobj.read(n)
        self._compress_left -= len(data)
        if not data: raise EOFError
        if self._decrypter is not None:
            data = self._decrypter(data)
        return data

    def close(self):
        try:
            if self._close_fileobj:
                self._fileobj.close()
        finally:
            super().close()

class ZipFile:
    fp = None
    def __init__(self, file, mode="r", compression=ZIP_STORED, allowZip64=True):
        if mode != 'r':
            raise ValueError("ReadOnlyZipFile only supports 'r'")
        self._allowZip64 = allowZip64
        self.NameToInfo = {}
        self.filelist = []
        self.compression = compression
        self.mode = mode
        self.pwd = None
        self._comment = b''
        
        if isinstance(file, str):
            self._filePassed = 0
            self.filename = file
            self.fp = io.open(file, 'rb')
        else:
            self._filePassed = 1
            self.fp = file
            self.filename = getattr(file, 'name', None)
        self._fileRefCnt = 1
        self._lock = RLock()
        self._RealGetContents()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def _RealGetContents(self):
        fp = self.fp
        try:
            endrec = _EndRecData(fp)
        except OSError:
            raise BadZipFile("File is not a zip file")
        if not endrec:
            raise BadZipFile("File is not a zip file")
        size_cd = endrec[_ECD_SIZE]
        offset_cd = endrec[_ECD_OFFSET]
        self._comment = endrec[_ECD_COMMENT]
        concat = endrec[_ECD_LOCATION] - size_cd - offset_cd
        if endrec[_ECD_SIGNATURE] == stringEndArchive64:
            concat -= (sizeEndCentDir64 + sizeEndCentDir64Locator)
        self.start_dir = offset_cd + concat
        fp.seek(self.start_dir, 0)
        data = fp.read(size_cd)
        fp = io.BytesIO(data)
        total = 0
        while total < size_cd:
            centdir = fp.read(sizeCentralDir)
            if len(centdir) != sizeCentralDir:
                raise BadZipFile("Truncated central directory")
            centdir = struct.unpack(structCentralDir, centdir)
            if centdir[_CD_SIGNATURE] != stringCentralDir:
                raise BadZipFile("Bad magic number")
            filename = fp.read(centdir[_CD_FILENAME_LENGTH])
            orig_filename_crc = crc32(filename)
            flags = centdir[_CD_FLAG_BITS]
            if flags & _MASK_UTF_FILENAME:
                filename = filename.decode('utf-8')
            else:
                filename = filename.decode('cp437')
            x = ZipInfo(filename)
            x.extra = fp.read(centdir[_CD_EXTRA_FIELD_LENGTH])
            x.comment = fp.read(centdir[_CD_COMMENT_LENGTH])
            x.header_offset = centdir[_CD_LOCAL_HEADER_OFFSET]
            (x.create_version, x.create_system, x.extract_version, x.reserved,
             x.flag_bits, x.compress_type, t, d,
             x.CRC, x.compress_size, x.file_size) = centdir[1:12]
            x.volume, x.internal_attr, x.external_attr = centdir[15:18]
            x._raw_time = t
            x.date_time = ( (d>>9)+1980, (d>>5)&0xF, d&0x1F, t>>11, (t>>5)&0x3F, (t&0x1F) * 2 )
            x._decodeExtra(orig_filename_crc)
            x.header_offset = x.header_offset + concat
            self.filelist.append(x)
            self.NameToInfo[x.filename] = x
            total = (total + sizeCentralDir + centdir[_CD_FILENAME_LENGTH]
                     + centdir[_CD_EXTRA_FIELD_LENGTH] + centdir[_CD_COMMENT_LENGTH])

    def namelist(self):
        return [data.filename for data in self.filelist]

    def infolist(self):
        return self.filelist

    def getinfo(self, name):
        info = self.NameToInfo.get(name)
        if info is None:
            raise KeyError('There is no item named %r in the archive' % name)
        return info

    def setpassword(self, pwd):
        self.pwd = pwd

    def read(self, name, pwd=None):
        with self.open(name, "r", pwd) as fp:
            return fp.read()

    def open(self, name, mode="r", pwd=None):
        if mode != "r":
            raise ValueError("open() requires mode 'r'")
        if not self.fp:
            raise ValueError("Closed")
        if isinstance(name, ZipInfo):
            zinfo = name
        else:
            zinfo = self.getinfo(name)

        self._fileRefCnt += 1
        zef_file = _SharedFile(self.fp, zinfo.header_offset, self._fpclose, self._lock)
        try:
            fheader = zef_file.read(sizeFileHeader)
            if len(fheader) != sizeFileHeader:
                raise BadZipFile("Truncated file header")
            fheader = struct.unpack(structFileHeader, fheader)
            if fheader[_FH_SIGNATURE] != stringFileHeader:
                raise BadZipFile("Bad magic number for file header")
            fname = zef_file.read(fheader[_FH_FILENAME_LENGTH])
            if fheader[_FH_EXTRA_FIELD_LENGTH]:
                zef_file.seek(fheader[_FH_EXTRA_FIELD_LENGTH], 1)
            
            is_encrypted = zinfo.flag_bits & _MASK_ENCRYPTED
            if is_encrypted:
                if not pwd: pwd = self.pwd
                if not pwd: raise RuntimeError("Password required")
            else:
                pwd = None
            return ZipExtFile(zef_file, zinfo, pwd, True)
        except:
            zef_file.close()
            raise

    def extract(self, member, path=None, pwd=None):
        if path is None:
            path = os.getcwd()
        return self._extract_member(member, path, pwd)

    def extractall(self, path=None, members=None, pwd=None):
        if members is None:
            members = self.namelist()
        if path is None:
            path = os.getcwd()
        for zipinfo in members:
            self._extract_member(zipinfo, path, pwd)

    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)
        arcname = member.filename.replace('/', '/')
        arcname = arcname.lstrip('/')
        if not arcname and not member.is_dir():
            raise ValueError("Empty filename.")
        targetpath = targetpath + "/" + arcname
        
        upperdirs = targetpath.rsplit('/', 1)[0]
        if upperdirs and not path_exists(upperdirs):
            makedirs(upperdirs)

        if member.is_dir():
            if not path_exists(targetpath):
                os.mkdir(targetpath)
            return targetpath

        with self.open(member, pwd=pwd) as source, open(targetpath, "wb") as target:
            copyfileobj(source, target)
        return targetpath

    def close(self):
        if self.fp is None: return
        fp = self.fp
        self.fp = None
        self._fpclose(fp)

    def _fpclose(self, fp):
        self._fileRefCnt -= 1
        if not self._fileRefCnt and not self._filePassed:
            fp.close()
import hashlib
import os
import shutil
import subprocess
from config import SECRET_SALT
from database import get_local_directory, get_backup_directory


def get_hwid():
    # PC serial -> HWID (lifetime lock)
    cands = []
    try:
        out = subprocess.check_output(
            "wmic baseboard get serialnumber", shell=True,
            stderr=subprocess.DEVNULL, timeout=5
        ).decode(errors="ignore").strip().splitlines()
        for line in out:
            line = line.strip()
            if line and "serial" not in line.lower():
                cands.append(line)
                break
    except Exception:
        pass
    try:
        out2 = subprocess.check_output(
            "wmic csproduct get uuid", shell=True,
            stderr=subprocess.DEVNULL, timeout=5
        ).decode(errors="ignore").strip().splitlines()
        for line in out2:
            line = line.strip()
            if line and "uuid" not in line.lower():
                cands.append(line)
                break
    except Exception:
        pass
    serial = "|".join(cands) if cands else ""
    if not serial:
        return "FALLBACK_HWID_101"
    return hashlib.sha256((serial + SECRET_SALT).encode()).hexdigest()[:16].upper()


def make_key(hwid):
    return hashlib.sha256((hwid + SECRET_SALT + "LIFETIME").encode()).hexdigest()[:20].upper()


def license_paths():
    paths = [os.path.join(get_local_directory(), "license.key")]
    try:
        b = get_backup_directory()
        if b:
            paths.append(os.path.join(b, "license.key"))
    except Exception:
        pass
    return paths


def license_path():
    return license_paths()[0]


def restore_license():
    # Windows notun dile D: theke license khuje local e ano
    local = license_paths()[0]
    if os.path.exists(local):
        return local
    for p in license_paths()[1:]:
        try:
            if os.path.exists(p):
                shutil.copy2(p, local)
                return local
        except Exception:
            pass
    return None


def check_license():
    # lifetime: ekbar register -> PC change na hole always True
    # strict ON thakle key chara cholbe na, OFF thakle test/sell easy
    strict = False
    try:
        from database import get_local_directory as _ld
        import json as _js, os as _os
        _p = _os.path.join(_ld(), "settings.json")
        if _os.path.exists(_p):
            with open(_p, "r") as _f:
                strict = bool(_js.load(_f).get("strict_license", False))
    except Exception:
        pass
    restore_license()
    p = license_path()
    try:
        if os.path.exists(p):
            with open(p, "r") as f:
                key = f.read().strip().upper()
            if key == make_key(get_hwid()):
                try:
                    for bp in license_paths()[1:]:
                        if not os.path.exists(bp):
                            shutil.copy2(p, bp)
                except Exception:
                    pass
                return True
            return False
        return False if strict else True
    except Exception:
        return False if strict else True


def save_license(key):
    key = key.strip().upper()
    with open(license_path(), "w") as f:
        f.write(key)
    try:
        for bp in license_paths()[1:]:
            os.makedirs(os.path.dirname(bp), exist_ok=True)
            with open(bp, "w") as f:
                f.write(key)
    except Exception:
        pass
    return key == make_key(get_hwid())

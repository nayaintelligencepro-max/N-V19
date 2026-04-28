"""NAYA — Structured Logger."""
import logging,sys,json,os
from pathlib import Path
from typing import Optional

class NayaJSONFormatter(logging.Formatter):
    def format(self,r):
        o={"time":self.formatTime(r,"%Y-%m-%dT%H:%M:%S"),"level":r.levelname,"logger":r.name,"message":r.getMessage()}
        if r.exc_info: o["exception"]=self.formatException(r.exc_info)
        return json.dumps(o,ensure_ascii=False)

class NayaColorFormatter(logging.Formatter):
    C={"DEBUG":"\033[36m","INFO":"\033[32m","WARNING":"\033[33m","ERROR":"\033[31m","CRITICAL":"\033[35m"}; R="\033[0m"
    def format(self,r): return f"{self.C.get(r.levelname,'')}{super().format(r)}{self.R}"

class NayaLogger:
    _configured=False
    @staticmethod
    def setup(name="NAYA",level=logging.INFO,log_dir=None,json_mode=False) -> logging.Logger:
        logger=logging.getLogger(name); logger.setLevel(level); logger.handlers.clear()
        env=os.environ.get("NAYA_ENV","local").lower()
        use_json=json_mode or env in ("cloud_run","vm","production")
        h=logging.StreamHandler(sys.stdout); h.setLevel(level)
        if use_json: h.setFormatter(NayaJSONFormatter())
        else: h.setFormatter(NayaColorFormatter(fmt="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",datefmt="%H:%M:%S"))
        logger.addHandler(h)
        if log_dir:
            try:
                Path(log_dir).mkdir(parents=True,exist_ok=True)
                fh=logging.FileHandler(Path(log_dir)/"naya.log",encoding="utf-8"); fh.setLevel(logging.DEBUG); fh.setFormatter(NayaJSONFormatter()); logger.addHandler(fh)
            except Exception:  # log_dir inaccessible — mode sans fichier
                pass
        logger.propagate=False; NayaLogger._configured=True; return logger

    @staticmethod
    def get(name="NAYA") -> logging.Logger:
        if not NayaLogger._configured: NayaLogger.setup()
        return logging.getLogger(name)

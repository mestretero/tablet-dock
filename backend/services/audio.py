"""Varsayılan ses çıkış cihazını değiştir (hızlı geçiş için 2 cihaz).

Windows'ta varsayılan oynatma cihazını ayarlamanın resmi API'si yok;
belgesiz IPolicyConfig COM arayüzü kullanılır (ek program gerekmez).
Cihazlar FriendlyName içindeki ayırt edici metinle eşlenir.
"""
from ctypes import HRESULT
from ctypes.wintypes import DWORD, LPCWSTR

import comtypes
from comtypes import CLSCTX_ALL, COMMETHOD, GUID, IUnknown
from pycaw.pycaw import AudioUtilities

# Hızlı geçiş yapılacak 2 çıkış (label = panelde görünecek ad).
TARGETS = [
    {"key": "steelseries", "label": "SteelSeries Gaming", "match": "SteelSeries Sonar - Gaming"},
    {"key": "realtek2", "label": "Realtek 2nd output", "match": "Realtek HD Audio 2nd output"},
]

_CLSID_POLICY = GUID("{870af99c-171d-4f9e-af0d-e63df40c2bc9}")  # CPolicyConfigClient


class IPolicyConfig(IUnknown):
    """Win7+ IPolicyConfig. Sadece SetDefaultEndpoint çağrılır; öncesindeki
    metotlar doğru vtable konumu için yer tutucu olarak tanımlı."""
    _iid_ = GUID("{f8679f50-850a-41cf-9c72-430f290290c8}")
    _methods_ = (
        COMMETHOD([], HRESULT, "GetMixFormat"),
        COMMETHOD([], HRESULT, "GetDeviceFormat"),
        COMMETHOD([], HRESULT, "ResetDeviceFormat"),
        COMMETHOD([], HRESULT, "SetDeviceFormat"),
        COMMETHOD([], HRESULT, "GetProcessingPeriod"),
        COMMETHOD([], HRESULT, "SetProcessingPeriod"),
        COMMETHOD([], HRESULT, "GetShareMode"),
        COMMETHOD([], HRESULT, "SetShareMode"),
        COMMETHOD([], HRESULT, "GetPropertyValue"),
        COMMETHOD([], HRESULT, "SetPropertyValue"),
        COMMETHOD([], HRESULT, "SetDefaultEndpoint",
                  (["in"], LPCWSTR, "wszDeviceId"),
                  (["in"], DWORD, "eRole")),
        COMMETHOD([], HRESULT, "SetEndpointVisibility"),
    )


def _device_id_for(match: str):
    comtypes.CoInitialize()
    for d in AudioUtilities.GetAllDevices():
        if d.FriendlyName and match.lower() in d.FriendlyName.lower():
            return d.id
    return None


def _current_id():
    comtypes.CoInitialize()
    try:
        return AudioUtilities.GetSpeakers().id
    except Exception:
        return None


def _set_default(device_id: str):
    comtypes.CoInitialize()
    policy = comtypes.CoCreateInstance(_CLSID_POLICY, IPolicyConfig, CLSCTX_ALL)
    for role in (0, 1, 2):   # Console, Multimedia, Communications
        policy.SetDefaultEndpoint(device_id, role)


def list_outputs() -> list[dict]:
    """2 hedef çıkış + hangisi şu an aktif."""
    cur = _current_id()
    out = []
    for t in TARGETS:
        did = _device_id_for(t["match"])
        out.append({
            "key": t["key"],
            "label": t["label"],
            "available": did is not None,
            "active": did is not None and did == cur,
        })
    return out


def set_output(key: str) -> bool:
    t = next((x for x in TARGETS if x["key"] == key), None)
    if not t:
        return False
    did = _device_id_for(t["match"])
    if not did:
        return False
    _set_default(did)
    return True

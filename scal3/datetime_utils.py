from scal3.cal_types import calTypes, jd_to
from scal3.date_utils import dateEncode
from scal3.time_utils import getJhmsFromEpoch

__all__ = ["epochDateTimeEncode"]


def epochDateTimeEncode(epoch: float) -> str:
	jd, hms = getJhmsFromEpoch(epoch)
	return dateEncode(jd_to(jd, calTypes.primary)) + f" {hms:HMS}"

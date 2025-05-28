from scal3.account.google import GoogleAccount
from scal3.account.starcal import StarCalendarAccount
from scal3.vcs_modules.git import (
	clearObj,
	getCommitInfo,
	getCommitList,
	getCommitShortStatLine,
	getFirstCommitEpoch,
	getLastCommitEpoch,
	getLatestParentBefore,
	getShortStat,
	getTagList,
	getTagShortStatLine,
	prepareObj,
)
from scal3.vcs_modules.hg import (  # type: ignore[assignment]
	clearObj,
	getCommitInfo,
	getCommitList,
	getCommitShortStatLine,
	getFirstCommitEpoch,
	getLastCommitEpoch,
	getLatestParentBefore,
	getShortStat,
	getTagList,
	getTagShortStatLine,
	prepareObj,
)

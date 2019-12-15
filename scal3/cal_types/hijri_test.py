from scal3.cal_types import hijri

if __name__ == "__main__":
	for ym in hijri.monthDb.monthLenByYm:
		y, m = divmod(ym, 12)
		m += 1
		log.info(hijri.to_jd(y, m, 1) - hijri.to_jd_c(y, m, 1))


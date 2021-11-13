from scal3.cal_types import hijri

def print_to_jd_diff():
	for ym in hijri.monthDb.monthLenByYm:
		y, m = divmod(ym, 12)
		m += 1
		print(hijri.to_jd(y, m, 1) - hijri.to_jd_c(y, m, 1))

if __name__ == "__main__":
	print_to_jd_diff()


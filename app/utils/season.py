from datetime import datetime


def current_season_id() -> int:
    now = datetime.now()
    if now.month >= 10:
        return int(f"{now.year}10")
    elif now.month >= 7:
        return int(f"{now.year}07")
    elif now.month >= 4:
        return int(f"{now.year}04")
    else:
        return int(f"{now.year}01")


def recent_season_ids() -> set[int]:
    now = datetime.now()
    years = [now.year - 1, now.year]
    months = [1, 4, 7, 10]
    seasons = []
    for year in years:
        for month in months:
            if month > now.month and year == now.year:
                continue
            seasons.append(int(f"{year}{month:02d}"))
    return set(seasons[-4:])


def older_season_ids() -> set[int]:
    now = datetime.now()
    years = [year for year in range(now.year - 4, now.year + 1, 1)]
    months = [1, 4, 7, 10]
    seasons = []
    for year in years:
        for month in months:
            if month > now.month and year == now.year:
                continue
            seasons.append(int(f"{year}{month:02d}"))
    return set(seasons[-16:]) - set(recent_season_ids())


def all_season_ids() -> set[int]:
    now = datetime.now()
    years = [year for year in range(now.year, 2011, -1)]
    months = [1, 4, 7, 10]
    seasons = []
    for year in years:
        for month in months:
            if month > now.month and year == now.year:
                continue
            seasons.append(int(f"{year}{month:02d}"))
    return (
        set(seasons) - set(recent_season_ids()) - set(older_season_ids()) - {"201201"}
    )


def future_season_ids() -> set[int]:
    now = datetime.now()
    years = [year for year in range(now.year, now.year + 2)]
    months = [1, 4, 7, 10]
    seasons = []
    for year in years:
        for month in months:
            if month <= now.month and year == now.year:
                continue
            seasons.append(int(f"{year}{month:02d}"))
    return set(seasons[:1])


if __name__ == "__main__":
    print(current_season_id())
    print(sorted(list(future_season_ids())))
    print(sorted(list(recent_season_ids())))
    print(sorted(list(older_season_ids())))
    print(sorted(list(all_season_ids())))

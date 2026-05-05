#!/usr/bin/env python3
"""Seed homepage URLs for major sample schools (publicly known)."""
import sqlite3
from pathlib import Path

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

# Public official URLs (publicly known, official school sites)
URLS = [
    ('開成中学校', 'https://kaiseigakuen.jp/'),
    ('麻布中学校', 'https://www.azabu-jh.ed.jp/'),
    ('桜蔭中学校', 'https://www.oin.ed.jp/'),
    ('雙葉中学校', 'https://www.futabagakuen-jh.ed.jp/'),
    ('女子学院中学校', 'https://www.joshigakuin.ed.jp/'),
    ('駒場東邦中学校', 'https://www.komabajh.toho-u.ac.jp/'),
    ('海城中学校', 'https://www.kaijo.ed.jp/'),
    ('芝中学校', 'https://www.shiba.ac.jp/'),
    ('浅野中学校', 'https://www.asano.ed.jp/'),
    ('聖光学院中学校', 'https://www.seiko.ac.jp/'),
    ('栄光学園中学校', 'https://ekh.jp/'),
    ('慶應義塾普通部', 'https://www.kf.keio.ac.jp/'),
    # extras
    ('武蔵中学校', 'https://www.musashi.ed.jp/'),
    ('豊島岡女子学園中学校', 'https://www.toshimagaoka.ed.jp/'),
    ('白百合学園中学校', 'https://www.shirayuri.ed.jp/'),
    ('聖心女子学院中等科', 'https://www.tky-sacred-heart.ed.jp/'),
    ('東洋英和女学院中学部', 'https://www.toyoeiwa.ac.jp/'),
    ('青山学院中等部', 'https://www.jh.aoyama.ed.jp/'),
    ('立教池袋中学校', 'https://ikebukuro.rikkyo.ac.jp/'),
    ('立教女学院中学校', 'https://www.rikkyojogakuin.ac.jp/'),
    ('暁星中学校', 'https://www.gyosei-h.ed.jp/'),
    ('六甲学院中学校', 'https://www.rokkojh.org/'),
    ('灘中学校', 'https://www.nada.ac.jp/'),
    ('神戸女学院中学部', 'https://www.kobejogakuin-h.ed.jp/'),
    ('愛光中学校', 'https://www.aiko.ed.jp/'),
    ('ラ・サール中学校', 'https://www.lasalle.ed.jp/'),
    ('久留米大学附設中学校', 'https://www.kurume-fu.ac.jp/'),
    ('渋谷教育学園幕張中学校', 'https://www.shibumaku.jp/'),
    ('渋谷教育学園渋谷中学校', 'https://www.shibushibu.jp/'),
    ('広尾学園中学校', 'https://www.hiroogakuen.ed.jp/'),
    ('鴎友学園女子中学校', 'https://www.ohyu.jp/'),
    ('吉祥女子中学校', 'https://www.kichijo-joshi.jp/'),
]

def main():
    db = sqlite3.connect(DB)
    updated = 0
    for name, url in URLS:
        cur = db.execute("UPDATE schools_v2 SET homepage_url=? WHERE name_ja=? AND (homepage_url IS NULL OR homepage_url='')",
                         (url, name))
        updated += cur.rowcount
    db.commit()
    db.close()
    print(f"Updated {updated} school URLs")

if __name__ == '__main__':
    main()

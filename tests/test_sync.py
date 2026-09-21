import unittest
from scripts.sync import parse_release, normalize_android

class SyncTests(unittest.TestCase):
    def release(self, body='', tag='4.1.11.53'):
        return dict(tag_name=tag, body=body, html_url='https://github.com/zsbai/wechat-versions/releases/tag/'+tag,
                    published_at='2026-07-09T00:00:00Z', draft=False, prerelease=False,
                    assets=[dict(name='WeChat.dmg', size=123, browser_download_url='https://github.com/zsbai/wechat-versions/releases/download/'+tag+'/WeChat.dmg', digest=None)])

    def test_blank_md5_does_not_capture_next_field(self):
        r=parse_release(self.release('- DestVersion: 4.1.11.53\n- Md5: \n- Sha256: '+'a'*64+'\n'))
        self.assertIsNone(r['md5'])
        self.assertEqual(r['sha256'], 'a'*64)

    def test_truncated_checksum_is_not_published(self):
        r=parse_release(self.release('Sha256: ea80413fca0ea09eb4241e333a8f098\n'))
        self.assertIsNone(r['sha256'])

    def test_date_tags_preserve_distinct_builds(self):
        a=parse_release(self.release('DestVersion: 4.1.0', 'v4.1.0_20250820'))
        b=parse_release(self.release('DestVersion: 4.1.0', 'v4.1.0_20250821'))
        self.assertNotEqual(a['slug'],b['slug'])
        self.assertEqual(a['version'],'4.1.0')

    def test_asset_digest_is_separate_from_release_checksum(self):
        r=self.release('Sha256: '+'a'*64)
        r['assets'][0]['digest']='sha256:'+'b'*64
        out=parse_release(r)
        self.assertEqual(out['sha256'],'a'*64)
        self.assertEqual(out['assets'][0]['sha256'],'b'*64)

    def test_non_tencent_download_is_not_treated_as_official(self):
        r=parse_release(self.release('DownloadFrom: https://example.com/file.dmg'))
        self.assertIsNone(r['official_url'])

    def test_android_missing_version_recovered_from_name(self):
        rows=normalize_android([dict(version='',name='微信 6.6 for Android',publish_date='2017-12-22',url=' https://dldir1.qq.com/weixin/android/weixin660android1200.apk ')])
        self.assertEqual(rows[0]['version'],'6.6')
        self.assertFalse(rows[0]['url'].startswith(' '))

if __name__=='__main__': unittest.main()

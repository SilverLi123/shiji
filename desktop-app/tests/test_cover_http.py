import unittest
import test_upgrade as fixture
from test_cover_preferences import image_bytes
import base64

class CoverHTTP(unittest.TestCase):
    setUp=fixture.Integration.setUp;start=fixture.Integration.start;tearDown=fixture.Integration.tearDown;req=fixture.Integration.req
    def test_actual_api_atomic_save_conflict_legacy_edit_and_origin(self):
        r=self.req('/api/resources','POST',{'title':'Source','kind':'file'})['resource'];path='/api/resources/'+r['id'];url=path+'/cover'
        body={'config':{'style':'spatial','customTitle':'封面'},'coverId':'','expected':{'coverConfig':None,'coverId':''},'upload':{'name':'valid.png','mime':'image/png','base64':base64.b64encode(image_bytes()).decode()}}
        first=self.req(url,'POST',body);self.assertTrue(first['changed']);r=first['resource'];self.assertEqual(r['title'],'Source');self.assertTrue(r['coverId'])
        self.assertFalse(self.req(url,'POST',body)['changed'])
        conflict=self.req(url,'POST',{**body,'config':{'style':'minimal'},'upload':None},status=409);self.assertEqual(conflict['resource']['coverConfig']['style'],'spatial')
        self.req(url,'POST',body,status=403,headers={'Origin':'https://evil.example'})
        self.req(url,'PUT',body,status=404)
        self.assertEqual(self.req(path,'PUT',{'title':'Old client'})['resource']['coverConfig'],r['coverConfig'])
        self.assertEqual(self.req('/api/files/'+r['coverId']),image_bytes())

if __name__=='__main__':unittest.main()

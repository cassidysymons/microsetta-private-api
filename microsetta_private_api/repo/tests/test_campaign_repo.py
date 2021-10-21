import unittest
import uuid

from microsetta_private_api.repo.campaign_repo import CampaignRepo
from microsetta_private_api.repo.transaction import Transaction


EMAIL_1 = 'foo@bar.com'
EMAIL_2 = 'wwbhsqo5s9@fi9s6.nzb'  # a valid email stable in the test database
ACCT_ID_1 = 'c979cc9e-a82f-4f53-a456-9fa9be9f52d4'
SRC_ID_1 = ''


# source IDs are constructed during patching and are not stable
# so let's pull one at runtime
with Transaction() as t:
    cur = t.cursor()
    cur.execute("""SELECT id as source_id
                   FROM ag.source
                   WHERE account_id=%s
                   LIMIT 1""",
                (ACCT_ID_1, ))
    SRC_ID_1 = cur.fetchone()[0]


class CampaignRepoTests(unittest.TestCase):
    def setUp(self):
        self.test_campaign_title1 = 'test-support'
        with Transaction() as t:
            cur = t.cursor()
            cur.execute("""INSERT INTO barcodes.campaigns
                           (title, accepting_participants)
                           VALUES (%s, 'Y')
                           RETURNING campaign_id""",
                        (self.test_campaign_title1, ))
            self.test_campaign_id1 = cur.fetchone()[0]

            cur.execute("""INSERT INTO barcodes.campaigns_projects
                           (campaign_id, project_id)
                           VALUES (%s, 1)""",
                        (self.test_campaign_id1, ))
            t.commit()

    def tearDown(self):
        with Transaction() as t:
            cur = t.cursor()
            cur.execute("""DELETE FROM barcodes.campaigns_projects
                           WHERE campaign_id=%s""",
                        (self.test_campaign_id1, ))
            cur.execute("""DELETE FROM barcodes.campaigns
                           WHERE title=%s""",
                        (self.test_campaign_title1, ))
            t.commit()

    def test_is_member_by_source(self):
        with Transaction() as t:
            cr = CampaignRepo(t)
            obs = cr.is_member_by_source(ACCT_ID_1, SRC_ID_1,
                                         self.test_campaign_id1)
            self.assertTrue(obs)

            for aid, sid, cid in [(str(uuid.uuid4()), str(uuid.uuid4()),
                                   str(uuid.uuid4())),
                                  (ACCT_ID_1, str(uuid.uuid4()),
                                   str(uuid.uuid4())),
                                  (str(uuid.uuid4()), SRC_ID_1,
                                   str(uuid.uuid4())),
                                  (ACCT_ID_1, SRC_ID_1,
                                   str(uuid.uuid4()))]:
                obs = cr.is_member_by_source(aid, sid, cid)
                self.assertFalse(obs)

    def test_is_member_by_email(self):
        with Transaction() as t:
            cur = t.cursor()
            cur.execute("""INSERT INTO barcodes.interested_users
                           (campaign_id, first_name, last_name, email,
                            address_checked, address_valid,
                            converted_to_account)
                           VALUES (%s, 'cool', 'bob', %s,
                                   'N', 'N', 'N')""",
                        (self.test_campaign_id1, EMAIL_1))

            cr = CampaignRepo(t)
            obs = cr.is_member_by_email(EMAIL_1, self.test_campaign_id1)
            self.assertTrue(obs)

            obs = cr.is_member_by_email(EMAIL_2, self.test_campaign_id1)
            self.assertTrue(obs)

            for email, cid in [('foobar@baz.com', self.test_campaign_id1),

                               # this email exists and is stable in the test
                               # database, and is not associated with project
                               # 1
                               ('bsbk(ounxw@)9t30.wid',
                                self.test_campaign_id1),

                               (EMAIL_1, str(uuid.uuid4()))]:
                obs = cr.is_member_by_email(email, cid)
                self.assertFalse(obs)


if __name__ == '__main__':
    unittest.main()

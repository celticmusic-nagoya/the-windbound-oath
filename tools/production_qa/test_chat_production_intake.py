import unittest
from copy import deepcopy
from chat_production_intake import parse

class IntakeTest(unittest.TestCase):
    def test_gate(self):
        event={"action":"created","issue":{"number":427,"pull_request":{ "url":"fixture"}},"comment":{"id":1,"user":{"type":"User"},"body":"/two preflight MORWEN "+"a"*40}}
        self.assertEqual(parse(event,"write")["mode"],"READ_ONLY")
        for permission in ("read","triage",None):
            self.assertIsNone(parse(event,permission))
        for body in ("",event["comment"]["body"]+"; echo bad",event["comment"]["body"]+"\n"):
            bad=deepcopy(event)
            bad["comment"]["body"]=body
            self.assertIsNone(parse(bad,"admin"))
        for key,value in (("number",421),("pull_request",None)):
            bad=deepcopy(event)
            bad["issue"][key]=value
            self.assertIsNone(parse(bad,"admin"))
        bad=deepcopy(event)
        bad["comment"]["user"]["type"]="Bot"
        self.assertIsNone(parse(bad,"admin"))
        bad=deepcopy(event)
        bad["action"]="edited"
        self.assertIsNone(parse(bad,"admin"))

if __name__=="__main__":
    unittest.main()

import http from "k6/http"; 
import { check, sleep, group } from "k6"; 
 
const ENDPOINT = __ENV.ENDPOINT;

function generateUUID() {
    const bytes = [...Array(36)].map(() => Math.floor(Math.random() * 16).toString(16));
    bytes[14] = '4';
    bytes[19] = (8 + Math.floor(Math.random() * 4)).toString(16);
    bytes[8] = bytes[13] = bytes[18] = bytes[23] = '-';
    return bytes.join('');
}

export function indecisivePlanner() { 
    group("Email Scan Submission", function () {
        let uuid = generateUUID();
        let url = `${ENDPOINT}/customers/${uuid}/emails`;
        const payload = JSON.stringify({
            "metadata": { "spamhammer": "1|14" },
            "contents": {
                "subject": "Important information about your account.",
                "from": "support@uq.edu.au",
                "to": "no-reply@uq.edu.au",
                "body": "Dear customer,\nWe have noticed some suspicious activity on your account. Please click [here](https://scam-check.uq.edu.au?userId=uqehugh3) to reset your password."
            }
        }); 
        const params = { headers: { 'Content-Type': 'application/json' }, timeout: '120s'  }; 
        let request = http.post(url, payload, params); 
        check(request, { 'is status 201': (r) => r.status === 201 }); 
    });
    sleep(30);
}

export function studyingStudent() { 
    let url = ENDPOINT + '/customers/3f70c6f1-e4e1-40e0-a1d5-32f4a539b7f4/emails'; 
  
    // What tasks do I have left to work on? 
    let request = http.get(url); 
  
    check(request, { 
       'is status 200': (r) => r.status === 200, 
    }); 
  
    // Alright I'll go work on my next task for around 2 minutes 
    sleep(30); 
 }

export const options = { 
    scenarios: { 
        // studier: { 
        //     exec: 'studyingStudent', 
        //     executor: "ramping-vus", 
        //     stages: [ 
        //        { duration: "2m", target: 100 }, 
        //        { duration: "4m", target: 250 }, 
        //        { duration: "2m", target: 0 }, 
        //     ], 
        //     gracefulRampDown: "60s"
        //  },
        HighLoadTest: { 
            exec: 'indecisivePlanner',
            executor: "ramping-vus",
            startVUs: 50,
            stages: [
                { duration: "1m", target: 100 }, // ramp up to 250 VUs in the first 10 minutes
                { duration: "2m", target: 250 }, // stay at 250 VUs for 40 minutes
                { duration: "1m", target: 50 }   // ramp down to 50 VUs over the last 10 minutes
            ],
            gracefulRampDown: "60s"
        }
    }
};

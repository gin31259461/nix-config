const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const policy = vm.createContext({});
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'), policy);
const scheduler = policy.createScheduler();
for (let i = 0; i < 100; i++) scheduler.request(policy.queriesForEvent('activewindowv2'));
const first = Array.from(scheduler.take());
assert.deepEqual(first, ['clients']);
for (let i = 0; i < 100; i++) scheduler.request(policy.queriesForEvent('activewindowv2'));
assert.equal(scheduler.take().length, 0);
scheduler.complete('clients');
assert.deepEqual(Array.from(scheduler.take()), ['clients']);
scheduler.complete('clients');
assert.equal(scheduler.take().length, 0);
for (const event of ['monitoradded', 'monitoraddedv2', 'configreloaded', 'unknown']) {
    scheduler.request(policy.queriesForEvent(event));
    const requested = Array.from(scheduler.take());
    assert.equal(requested.length, 5);
    requested.forEach(name => scheduler.complete(name));
}
const good = [{address: '0x1', workspace: {id: 1}, size: [640, 480]}];
let snapshot = policy.parseResult('clients', JSON.stringify(good), 0);
assert.equal(snapshot[0].workspace.id, 1);
for (const raw of ['', 'private invalid json', '{}', '[null]', '[{"address":"x"}]']) {
    const next = policy.parseResult('clients', raw, 0);
    assert.equal(next, null);
    if (next !== null) snapshot = next;
}
assert.equal(policy.parseResult('clients', JSON.stringify(good), 1), null);
assert.equal(snapshot[0].workspace.id, 1);
good[0].workspace.id = 2;
snapshot = policy.parseResult('clients', JSON.stringify(good), 0);
assert.equal(snapshot[0].workspace.id, 2);
assert.equal(policy.parseResult('activeworkspace', '{"id":"invalid"}', 0), null);
console.log('200 synthetic focus events: 2 client requests, no lost final refresh; invalid results preserve state.');

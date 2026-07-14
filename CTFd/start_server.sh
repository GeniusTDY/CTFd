#!/bin/bash
export PYTHONPATH=/workspace
cd /workspace/CTFd
exec python3 -c "from CTFd import create_app; app = create_app(); app.run(host='0.0.0.0', port=4000, debug=False)"

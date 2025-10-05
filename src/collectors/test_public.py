from src.collectors.base_generic import collect_source

def run():
    # This uses JSONPlaceholder - a free fake REST API for testing
    test_source = {
        "key": "test_public",
        "base_url": "https://jsonplaceholder.typicode.com",
        "auth_type": "none",
        "auth_env_key": "",
        "endpoints": [{
            "path": "/posts",
            "params": {
                "limit_param": "_limit",
                "page_param": None,
                "cursor_param": None,
                "date_param": None,
                "default_limit": 5,
                "default_lookback_days": 1
            }
        }],
        "headers": {},
        "rate_limit": {"req_per_min": 60}
    }
    
    path = collect_source(test_source)
    print(f"✓ Test collection successful: {path}")
    return path

if __name__ == "__main__":
    run()
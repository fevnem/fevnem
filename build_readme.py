from python_graphql_client import GraphqlClient
import feedparser
import pathlib
import re
import os
import datetime

root = pathlib.Path(__file__).parent.resolve()

def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->{}<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)

def fetch_blog_entries():
    entries = feedparser.parse("https://fevnem.github.io/rss.xml")["entries"]
    result = []
    
    for entry in entries:
        # Debug print to see the structure
        print(f"Entry date fields: {[k for k in entry.keys() if 'date' in k or 'time' in k or 'published' in k]}")
        
        # Try different date fields that might be present in the RSS feed
        date_str = None
        if 'published' in entry:
            date_str = entry['published']
        elif 'pubDate' in entry:
            date_str = entry['pubDate']
        elif 'updated' in entry:
            date_str = entry['updated']
        
        # If we found a date string, try to parse it
        published_date = ""
        if date_str:
            try:
                # Try several date formats
                try:
                    # RFC 2822 format
                    dt = datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    published_date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        # ISO format
                        dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        published_date = dt.strftime("%Y-%m-%d")
                    except ValueError:
                        # If all else fails, just use the string as is
                        published_date = date_str
            except Exception as e:
                print(f"Error parsing date: {e}")
                published_date = "Unknown date"
        
        result.append({
            "title": entry["title"],
            "url": entry["link"].split("#")[0],
            "published": published_date
        })
    
    return result

if __name__ == "__main__":
    readme = root / "README.md"
    readme_contents = readme.open().read()

    # Print the first entry to debug
    first_entry = feedparser.parse("https://fevnem.github.io/rss.xml")["entries"][0]
    print("First entry keys:", first_entry.keys())
    print("First entry:", first_entry)

    # Fetch and format blog entries
    entries = fetch_blog_entries()[:5]
    entries_md = "\n".join(
        [
            "* <a href='{url}' target='_blank'>{title}</a> - {published}".format(
                **entry
            )
            for entry in entries
        ]
    )
    rewritten = replace_chunk(readme_contents, "blog", entries_md)

    # Write updated README
    readme.open("w").write(rewritten)

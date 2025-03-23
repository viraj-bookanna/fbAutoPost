## Facebook Auto Post using Selenium

### Get Groups List

Use the following code to get a list of Facebook groups:

```javascript
console.log(
    JSON.stringify(
        Array.from(document.getElementsByTagName('div'))
            .filter(function (item) {
                if (item.getAttribute('role') == 'listitem' && item.getAttribute('data-visualcompletion') == 'ignore-dynamic') {
                    return true;
                }
            })
            .map(function (item) {
                var group = item.innerText.split('\n');
                return {
                    name: group[0],
                    type: group[1],
                    link: item.getElementsByTagName('a')[0].href.split('?')[0],
                };
            })
    )
);
```
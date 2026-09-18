# Recipe write API

Cloudflare Worker endpoint for adding Markdown recipes to this repository.

## Cloudflare setup

The Worker needs one secret named `GITHUB_TOKEN`. Create a fine-grained GitHub token restricted to this repository with **Contents: Read and write**, then add it in the Cloudflare Worker settings under Variables and Secrets.

Deploy command: `npx wrangler deploy`

## API

`GET /` is a health check.

`POST /recipe` accepts:

```json
{
  "filename": "my-recipe.md",
  "content": "# My recipe\n\n..."
}
```

For safety, this first version only creates new files in `recipes/`; it will not overwrite an existing recipe.

# Working on the deck in Google Slides

## Inserting a figure: the shared folder

The Slides API has no upload call. `createImage` takes a URL and Google's
servers fetch it anonymously, so a local PNG cannot be inserted directly,
and a private Drive file cannot either: it comes back as a sign-in page.

The way through is a Drive folder shared as *anyone with the link →
Viewer*, used only as a staging area. Files inherit the folder's sharing,
so uploading into it is enough; no sharing call is needed, and nothing
outside the folder is ever exposed.

**Set this up once** and record the folder id with the user's other
project settings:

```
https://drive.google.com/drive/folders/<FOLDER_ID>
```

Anything staged there is readable by anyone who has the id, so treat it as
a transfer buffer, not storage: upload, insert, trash. Do not stage
material that must not leak if the id does.

The cycle for each figure:

1. Upload with Drive `create_file`: `parentId` the folder,
   `contentMimeType: "image/png"`, `disableConversionToGoogleType: true`,
   and `base64Content` as the `sha256:<digest>:<absolute path>` file
   reference rather than typed-out base64.
2. Confirm it is fetchable before spending a write on it:
   `curl -sS -L -o /tmp/p.png -w "%{content_type}" \
    "https://drive.google.com/uc?export=download&id=<FILE_ID>"` should
   report `image/png`, not `text/html`.
3. `createImage` with that URL, giving `elementProperties.size` and a
   `transform` with `scaleX`/`scaleY` of 1 and the position in EMU.
4. Google copies the bytes into the deck, so trash the uploaded file
   afterwards with Drive `trash_file`. The deck does not depend on it.

If the folder has been removed or unshared, do not quietly share something
else: say so and let the user re-create it, or offer the manual route
(Insert → Image → Upload from computer).

**Resolution ceiling.** Google re-encodes inserted images to about 2048 px
on the long side. A 9 in wide image is then 228 dpi: fine when presenting
at 1080p, visibly soft in a 300 dpi PDF. Supplying a 2835 px render does
not beat the cap. If a diagram still reads as poor at 2048 px, the problem
is that a print figure with 5 to 7 pt type is being enlarged, and the fix
is to redraw it at slide scale with heavier type and lines, not to add
pixels.

## Two routes, and when to use each

**Building a new deck → .pptx.** Export a reference deck as .pptx, build
with `scripts/deck_builder.py`, upload with Drive `create_file` and
`contentMimeType` `application/vnd.openxmlformats-officedocument.presentationml.presentation`
so Drive converts it. Figures are embedded directly, which avoids one
upload-insert-trash cycle per figure, and twenty slides are one operation.
The cost is a new file and a new URL.

**Changing an existing deck → the Slides API.** Edits land in the file the
user already has open and the link stays the same. Use this for every
revision after the first, including adding a slide.

Never recreate a deck to avoid an edit: the user loses the link and any
comments.

## Slides API notes

- **Mask every read.** An unmasked `read_presentation` returns all layouts
  and masters. A useful mask:
  `["revisionId,pageSize,slides(objectId,pageElements(objectId,size,transform,shape(shapeType,placeholder.type,text.textElements.textRun.content),image.contentUrl,table(rows,columns)))"]`
- **Guard every write** with `writeControl.requiredRevisionId`, taken from
  a read after your last write. `replaceAllText`-only batches are the
  exception.
- **Re-read before editing a slide you edited earlier in the session.**
  If the user has touched the deck in the browser, object ids change:
  replacing an image in the UI gives the new image a fresh id, and a
  `deleteObject` on the old id fails and rejects the whole batch.
- **Geometry is size × transform scale.** An element reporting
  `size.width` 47250 EMU with `scaleX` 170.3 is 8.05 M EMU, i.e. 8.8 in.
  Convert with 914400 EMU per inch, 12700 per point.
- **Batches are atomic.** One bad request rejects everything, which is
  usually what you want, but it means a failed id costs the whole batch.
- **Text edits:** `replaceAllText` with `pageObjectIds` is the cheapest way
  to fix wording, and needs no ids.
- **Table colours:** `updateTableCellProperties` with a `tableRange` for
  fills, `updateTextStyle` with `cellLocation` for per-cell text. Setting a
  header row to the dark colour needs white text set cell by cell.

## Checking the result

Reading geometry back is not enough; look at the rendered slides.

1. Drive `download_file_content` with `exportMimeType: "application/pdf"`.
   The result usually exceeds the context limit and the host saves it to a
   JSON file, reporting the path.
2. `python scripts/render_check.py <that.json> <outdir>` writes page images
   and contact sheets of four slides each.
3. Read the sheets and look for: text running into the footer band, bullets
   overlapping a figure, a chip covering an axis label, a table past the
   bottom margin, and anything clipped.
4. Fix, then render only the changed pages (`--pages 11,13,16`) and check
   again.

`read_slide_page_thumbnail` is quicker for a single slide, and its URL can
be fetched with plain `curl`. At `WIDTH2000_PX` it is good enough for
layout but not for judging image sharpness.

## Things that do not work

- Keynote and LibreOffice automation may not be available, so Google's PDF
  export is often the only renderer on hand.
- A deck's own `image.contentUrl` values return 403 to an anonymous fetch,
  so they cannot be reused as a source for `createImage`.
- Drive `update_file` changes metadata only. There is no way to replace a
  Google Slides file's content in place from a new .pptx.
- Sharing the presentation itself does nothing for image insertion. If a
  deck of unpublished work is set to "anyone with the link can edit", say
  so: that is worth flagging every time.

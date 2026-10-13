# Image credits

The photographs fall into two groups.

**The halved produce in the hero was photographed by Sofia Mota**, the author of this project, on her own phone. Copyright is hers and no third-party permission is involved.

**Everything else is Creative Commons Zero (CC0 1.0)**, a public domain dedication: the photographer has waived their copyright, so the images may be used for any purpose, including commercially, with no permission or attribution required.

Attribution is not required by the licence. It is given here anyway, because crediting people who give their work away is the decent thing to do, and because it lets anyone re-check the licence for themselves.

Licences were read from each file's Wikimedia Commons record on 13 October 2026.

## Sofia's own photographs

| On the site | Subject | Photographer | Rights |
|---|---|---|---|
| `site/img/half-tomato.webp` | Halved tomato | Sofia Mota | Author's own work |
| `site/img/half-lemon.webp` | Halved lemon | Sofia Mota | Author's own work |
| `site/img/half-papaya.webp` | Halved papaya | Sofia Mota | Author's own work |
| `site/img/half-avocado.webp` | Halved avocado | Sofia Mota | Author's own work |
| `site/img/half-onion.webp` | Halved onion | Sofia Mota | Author's own work |

Source files live in `design/*.png`. `scripts/prepare_images.py` trims each to its subject, pads it to a square so the slow hero rotation turns about the centre, resizes to 440px and writes WebP with transparency.

## CC0 photographs used

| On the site | Subject | Photographer | Licence | Source file | Size |
|---|---|---|---|---|---|
| `site/img/apple.webp` | Red apple | Sprinno | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [Red apple on white background.jpg](https://commons.wikimedia.org/wiki/File:Red_apple_on_white_background.jpg) | 7 KB |
| `site/img/avocado.webp` | Avocado | Fructibus | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [Bilobed avocado 2017 A.jpg](https://commons.wikimedia.org/wiki/File:Bilobed_avocado_2017_A.jpg) | 71 KB |
| `site/img/carrot.webp` | Carrot | Fructibus | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [Curved carrot 2017 A.jpg](https://commons.wikimedia.org/wiki/File:Curved_carrot_2017_A.jpg) | 10 KB |
| `site/img/lemon.webp` | Lemon | Bordercolliez | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [Lemon with white background.jpg](https://commons.wikimedia.org/wiki/File:Lemon_with_white_background.jpg) | 17 KB |
| `site/img/pepper-green.webp` | Green bell pepper | Fructibus | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [Green bell pepper 2017 A.jpg](https://commons.wikimedia.org/wiki/File:Green_bell_pepper_2017_A.jpg) | 31 KB |
| `site/img/pepper-red.webp` | Red bell pepper | Fructibus | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [Flat red bell pepper 2017 A2.jpg](https://commons.wikimedia.org/wiki/File:Flat_red_bell_pepper_2017_A2.jpg) | 23 KB |

Six images, **159 KB** in total.

## How they were prepared

`scripts/prepare_images.py` rebuilds every file from scratch:

```bash
python scripts/prepare_images.py
```

It downloads each photo once into `build/img_cache/` (gitignored), lifts the subject off its white studio background, trims to the subject, resizes so the longest edge is 520px, and writes WebP with transparency into `site/img/`.

The cutout keeps only background that is both bright and nearly colourless **and** connected to the edge of the frame. The connectivity test is what protects white highlights inside the subject, which a plain brightness threshold would punch holes in. Per-image thresholds are recorded in `reference/image_sources.json` so the result is reproducible rather than hand-retouched.

No photograph has been altered beyond background removal, cropping and resizing. Colour, shape and content are untouched.

## Not from the reference site

None of these images come from the website whose visual style this project takes inspiration from. Its photography, logo and wording are its own and are not reproduced here.

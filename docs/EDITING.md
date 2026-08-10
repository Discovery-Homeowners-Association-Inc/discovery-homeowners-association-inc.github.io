# Editing the website

You do not need to install anything, and you do not need to know how websites
are built. Everything happens in a browser, and it works on a phone.

**https://dhoa.naponline.net/admin/**

Changes appear on the live site about two minutes after you press Publish.

---

## First time: getting an account

1. **Create a GitHub account** at [github.com/signup](https://github.com/signup)
   if you do not already have one. It is free. Use whatever email you like.
2. **Ask to be added** to the association's GitHub organization. Whoever is
   looking after the website can do this.
3. That is it. From then on you sign in with the **Login with GitHub** button.

> Your name and email will appear on the record of each change you make. If you
> would rather that not be your personal address, GitHub can give you a private
> one — Settings → Emails → *Keep my email address private*.

---

## The basics

Open **https://dhoa.naponline.net/admin/**, press **Login with GitHub**, and you
will see a list down the left:

| Section | What is in it |
|---|---|
| **Site Settings** | Address, phone, office hours, assessment amounts, Zelle details, the Pay Dues links |
| **Board of Directors** | The roster |
| **Committees** | The three standing committees and who is on them |
| **Report a Problem** | The who-to-call list |
| **Community Links** | Schools, utilities, churches, libraries |
| **Parks** | The park list and inspection notes |
| **Meeting Exceptions** | Cancelled or moved board meetings |
| **Announcements** | News posts |
| **Events** | The community calendar |
| **Documents & Forms** | PDFs |

Pick a thing, change it, press **Publish**. Give it two minutes and refresh the
website.

---

## Common jobs

### Post an announcement

**Announcements → New Announcement.** Fill in the headline, the date, and a
one-line summary — the summary is what people see on the home page and in search
results, so make it say something.

If the notice stops being relevant on a known date — a registration deadline, a
road closure — put that date in **Take down automatically after** and the site
will remove it for you.

**Pin to the top** keeps something at the top of the news page. Use it sparingly;
if everything is pinned, nothing is.

### Add an event

**Events → New Event.**

**You do not need to add board meetings.** They are on the calendar already —
the site works out the third Tuesday of every month by itself. If one is
cancelled or moved, use **Meeting Exceptions** instead.

### Upload a form or a PDF

**Documents & Forms → New Document.** Upload the PDF, give it a real title, pick
a category, and write a sentence saying what it is for. That sentence is what
people read in the list and what search matches on — "Application for a fence,
deck, shed or any other change to the outside of your home" is far more useful
than "ACC form".

### Change the office phone number, or the hours, or the dues

**Site Settings.** Change it once, and it updates everywhere on the site —
header, footer, contact page, every page that mentions it. There is no second
copy to remember.

---

## Things worth knowing

**Always fill in the photo description.** When you add a photo there is a box
asking what is in it. That text is what a blind resident's screen reader says
aloud, and what shows if the image fails to load. It is not optional — the site
refuses to build without it.

**Do not type a phone number or email into page text.** Write `{{< org "office.phone" >}}`
or `{{< email "acc" >}}` instead. It looks odd, but it means the number comes
from Site Settings — so when it changes, it changes everywhere at once instead of
being left stale on one forgotten page. That is exactly how the old site ended
up with wrong numbers on it.

**Nothing you can do is permanent.** Every change is recorded, and any of them
can be undone. Do not be afraid of the Publish button.

**Photos get resized automatically.** Upload the big version straight off your
phone — the website makes its own smaller copies. Do not shrink it first.

**PDF links never change.** Once a form is published at
`/documents/something.pdf`, that address keeps working, so it is safe to print
in a newsletter.

---

## If something looks wrong

The site checks itself when it builds, and it refuses to publish rather than
publish something broken. So if you press Publish and the change does not
appear after a few minutes, it is usually one of these:

- **A required box was left empty** — go back and look for the field marked in
  red.
- **The assessment numbers do not add up** — the annual amount has to be exactly
  four times the quarterly one. This is deliberate; the old site once showed two
  different figures.
- **A photo has no description** — see above.

If you are stuck, ask whoever looks after the website. Nothing is broken that
cannot be put back.

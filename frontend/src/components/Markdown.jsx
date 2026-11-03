/*
 * Markdown — renders a repository .md file verbatim, with:
 *   - GitHub tables/footnotes (remark-gfm)
 *   - an id on every heading (rehype-slug) so sections can be linked to
 *   - links to other docs rewritten to their in-app pages
 *   - wide tables wrapped so they scroll instead of widening the page
 */
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSlug from 'rehype-slug';
import { Link } from 'react-router-dom';
import { resolveDocLink } from '../lib/docs-index.js';

export default function Markdown({ children, productSlug }) {
  return (
    <div className="md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSlug]}
        components={{
          a({ href = '', children: kids, ...rest }) {
            const internal = resolveDocLink(href, productSlug);
            if (internal) return <Link to={internal}>{kids}</Link>;
            if (href.startsWith('#')) return <a href={href} {...rest}>{kids}</a>;
            // Links to source files point at the repository on GitHub.
            if (!/^https?:/.test(href)) {
              const path = href.replace(/^\.\.?\//, '');
              return <a href={`https://github.com/avcool3/hone/blob/main/${path}`} target="_blank" rel="noreferrer">{kids}</a>;
            }
            return <a href={href} target="_blank" rel="noreferrer" {...rest}>{kids}</a>;
          },
          table({ children: kids }) {
            return <div className="tscroll"><table>{kids}</table></div>;
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}

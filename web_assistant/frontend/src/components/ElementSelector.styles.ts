import styled from 'styled-components';

// CRITICAL: These styles define the visual appearance of the selector interface
// TODO(future): Add theme support
// CHECK(periodic): Verify style consistency

export const Container = styled.div`
  padding: 1rem;
`;

export const IframeContainer = styled.div`
  height: 600px;
  margin-bottom: 1rem;
`;

export const StyledIframe = styled.iframe`
  width: 100%;
  height: 100%;
  border: 1px solid #ccc;
`;

export const SelectorInfo = styled.div`
  margin-top: 1rem;
`;

export const SelectorCode = styled.code`
  display: block;
  padding: 0.5rem;
  background: #f5f5f5;
  border-radius: 4px;
  margin: 0.5rem 0;
  font-family: monospace;
`;

export const Loading = styled.div`
  color: #666;
  margin: 0.5rem 0;
`;

export const ErrorMessage = styled.div`
  color: #dc3545;
  margin: 0.5rem 0;
`;

export const MatchesList = styled.div`
  margin-top: 1rem;

  h4 {
    margin-bottom: 0.5rem;
  }

  ul {
    list-style: none;
    padding: 0;
  }
`;

export const MatchItem = styled.li`
  padding: 0.5rem;
  border: 1px solid #eee;
  margin: 0.5rem 0;
  border-radius: 4px;
`;

export const MatchText = styled.span`
  color: #666;
  margin-left: 0.5rem;
`;

export const AttributesContainer = styled.div`
  margin-top: 0.25rem;
  font-size: 0.9em;
`;

export const Attribute = styled.span`
  background: #e9ecef;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  margin-right: 0.5rem;
  display: inline-block;
`;

export const Suggestions = styled.div`
  margin-top: 1rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;

  h5 {
    margin: 0 0 0.5rem 0;
    color: #495057;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
    cursor: pointer;

    &:hover {
      background: #e9ecef;
    }

    code {
      font-family: monospace;
      background: #e9ecef;
      padding: 0.2rem 0.4rem;
      border-radius: 3px;
      color: #212529;
    }

    .type {
      font-size: 0.8rem;
      color: #6c757d;
      padding: 0.1rem 0.3rem;
      background: #dee2e6;
      border-radius: 3px;
    }

    .description {
      font-size: 0.9rem;
      color: #6c757d;
    }
  }
`;

export const PatternAnalysis = styled.div`
  margin-top: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #dee2e6;

  h4 {
    margin: 0 0 1rem 0;
    color: #343a40;
  }

  .stats {
    display: flex;
    gap: 2rem;
    margin-bottom: 1rem;
    padding: 0.5rem;
    background: #fff;
    border-radius: 4px;

    div {
      strong {
        color: #495057;
      }
    }
  }

  .recommendations {
    h5 {
      margin: 0 0 0.5rem 0;
      color: #495057;
    }

    ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    li {
      margin: 0.5rem 0;
      padding: 0.5rem;
      background: #fff;
      border-radius: 4px;
      border: 1px solid #dee2e6;

      .element-type {
        font-weight: 600;
        color: #343a40;
        margin-bottom: 0.25rem;
      }

      .selectors {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.5rem 0;

        code {
          font-family: monospace;
          background: #e9ecef;
          padding: 0.2rem 0.4rem;
          border-radius: 3px;
          cursor: pointer;
          transition: background-color 0.2s;

          &:hover {
            background: #dee2e6;
          }

          &.clickable {
            color: #007bff;
            &:hover {
              color: #0056b3;
            }
          }
        }
      }

      .confidence {
        font-size: 0.9rem;
        color: #6c757d;
      }
    }
  }
`;
